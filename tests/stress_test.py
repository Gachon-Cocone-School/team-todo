"""
동시 접속 및 DB 커넥션 풀 스트레스 테스트

실행 방법:
    # 서버를 먼저 실행해두고:
    uv run uvicorn app.main:app --reload

    # 별도 터미널에서:
    uv run python tests/stress_test.py
    uv run python tests/stress_test.py --concurrency 50 --requests 500
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import httpx

# 실행마다 고유한 접두사 → 중복 이메일 방지
RUN_ID = uuid.uuid4().hex[:8]

BASE_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# 결과 수집
# ---------------------------------------------------------------------------


@dataclass
class RequestResult:
    scenario: str
    status_code: int
    latency_ms: float
    error: str | None = None


@dataclass
class ScenarioStats:
    name: str
    results: list[RequestResult] = field(default_factory=list)

    def add(self, r: RequestResult) -> None:
        self.results.append(r)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def success(self) -> int:
        return sum(1 for r in self.results if r.error is None and r.status_code < 400)

    @property
    def network_errors(self) -> int:
        """실제 네트워크/타임아웃 오류 (r.error is not None)"""
        return sum(1 for r in self.results if r.error is not None)

    @property
    def http_errors(self) -> int:
        """HTTP 4xx/5xx 응답"""
        return sum(1 for r in self.results if r.error is None and r.status_code >= 400)

    @property
    def errors(self) -> int:
        return self.total - self.success

    @property
    def error_rate(self) -> float:
        return self.errors / self.total * 100 if self.total else 0

    @property
    def latencies(self) -> list[float]:
        """성공 여부와 무관하게 응답이 온 요청의 레이턴시 (네트워크 오류 제외)"""
        return [r.latency_ms for r in self.results if r.error is None]

    def percentile(self, p: float) -> float:
        lats = sorted(self.latencies)
        if not lats:
            return 0.0
        idx = int(len(lats) * p / 100)
        return lats[min(idx, len(lats) - 1)]

    def print_summary(self) -> None:
        lats = self.latencies
        print(f"\n{'─' * 55}")
        print(f"  시나리오: {self.name}")
        print(f"{'─' * 55}")
        print(f"  총 요청수    : {self.total}")
        print(f"  성공         : {self.success}")
        print(f"  실패         : {self.errors}  ({self.error_rate:.1f}%)")
        print(f"  네트워크 오류: {self.network_errors}  (타임아웃/커넥션 실패)")
        print(f"  HTTP 오류    : {self.http_errors}  (4xx/5xx 응답)")
        if lats:
            print(f"  평균 레이턴시: {statistics.mean(lats):.1f} ms")
            print(f"  중앙값       : {statistics.median(lats):.1f} ms")
            print(f"  P95          : {self.percentile(95):.1f} ms")
            print(f"  P99          : {self.percentile(99):.1f} ms")
            print(f"  최솟값       : {min(lats):.1f} ms")
            print(f"  최댓값       : {max(lats):.1f} ms")
        else:
            print("  (레이턴시 데이터 없음 — 전부 네트워크 오류)")

        # 오류 상세
        http_errs = [
            (r.status_code, r.error)
            for r in self.results
            if r.error is None and r.status_code >= 400
        ]
        net_errs = [r.error for r in self.results if r.error is not None]
        if http_errs:
            counter: dict[Any, int] = Counter(f"HTTP {sc}" for sc, _ in http_errs)
            print("  HTTP 오류 상세:")
            for msg, cnt in counter.most_common(5):
                print(f"    [{cnt:>4}x] {msg}")
        if net_errs:
            nc: dict[Any, int] = Counter(str(e).split(":")[0] for e in net_errs)
            print("  네트워크 오류 상세:")
            for msg, cnt in nc.most_common(5):
                print(f"    [{cnt:>4}x] {msg}")


# ---------------------------------------------------------------------------
# HTTP 헬퍼
# ---------------------------------------------------------------------------


async def send(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    scenario: str,
    **kwargs: Any,
) -> RequestResult:
    start = time.perf_counter()
    try:
        resp = await client.request(method, f"{BASE_URL}{path}", **kwargs)
        latency = (time.perf_counter() - start) * 1000
        return RequestResult(
            scenario=scenario, status_code=resp.status_code, latency_ms=latency
        )
    except Exception as exc:
        latency = (time.perf_counter() - start) * 1000
        return RequestResult(
            scenario=scenario, status_code=0, latency_ms=latency, error=str(exc)
        )


# ---------------------------------------------------------------------------
# 시나리오 1: 순수 읽기 부하 (GET /todos, GET /users)
# ---------------------------------------------------------------------------


async def scenario_read_load(
    client: httpx.AsyncClient,
    stats: ScenarioStats,
    n: int,
    semaphore: asyncio.Semaphore,
) -> None:
    endpoints = ["/todos", "/users", "/tags"]

    async def one(i: int) -> None:
        async with semaphore:
            path = endpoints[i % len(endpoints)]
            r = await send(client, "GET", path, stats.name)
            stats.add(r)

    await asyncio.gather(*[one(i) for i in range(n)])


# ---------------------------------------------------------------------------
# 시나리오 2: 동시 쓰기 부하 (POST /users, POST /todos) — DB 락 경합 유발
# ---------------------------------------------------------------------------


async def scenario_write_load(
    client: httpx.AsyncClient,
    stats: ScenarioStats,
    n: int,
    semaphore: asyncio.Semaphore,
) -> list[int]:
    """생성된 user_id 목록 반환"""
    created_ids: list[int] = []
    lock = asyncio.Lock()

    async def create_user(i: int) -> None:
        async with semaphore:
            r = await send(
                client,
                "POST",
                "/users",
                stats.name,
                json={
                    "name": f"stress_user_{RUN_ID}_{i}",
                    "email": f"stress_{RUN_ID}_{i}@test.com",
                },
            )
            stats.add(r)
            if r.status_code == 201:
                # response body 재요청 없이 ID를 알 수 없으므로 별도 GET으로 확인 생략
                # 여기서는 생성 성공 카운트만 추적
                async with lock:
                    created_ids.append(i)

    await asyncio.gather(*[create_user(i) for i in range(n)])
    return created_ids


# ---------------------------------------------------------------------------
# 시나리오 3: 혼합 읽기/쓰기 (실제 서비스 패턴 모사)
# ---------------------------------------------------------------------------


async def scenario_mixed_load(
    client: httpx.AsyncClient,
    stats: ScenarioStats,
    n: int,
    semaphore: asyncio.Semaphore,
) -> None:
    """70% 읽기 / 30% 쓰기"""

    async def one(i: int) -> None:
        async with semaphore:
            if i % 10 < 7:  # 70% 읽기
                path = ["/todos", "/users", "/tags"][i % 3]
                r = await send(client, "GET", path, stats.name)
            else:  # 30% 쓰기
                r = await send(
                    client,
                    "POST",
                    "/users",
                    stats.name,
                    json={
                        "name": f"mixed_{RUN_ID}_{i}",
                        "email": f"mixed_{RUN_ID}_{i}@test.com",
                    },
                )
            stats.add(r)

    await asyncio.gather(*[one(i) for i in range(n)])


# ---------------------------------------------------------------------------
# 시나리오 4: DB 커넥션 풀 포화 테스트 — 최대 동시성으로 쿼리 폭격
# ---------------------------------------------------------------------------


async def scenario_pool_exhaustion(
    client: httpx.AsyncClient,
    stats: ScenarioStats,
    n: int,
    max_concurrency: int,
) -> None:
    """
    세마포어 없이 전량 동시 발사 → 커넥션 풀 한계 테스트.
    SQLite는 파일 락 때문에 쓰기 직렬화, 풀 고갈 시 OperationalError 발생 가능.
    """
    print(f"\n  ⚡ 커넥션 풀 포화 테스트: {n}개 요청 동시 발사 (세마포어 없음)")

    tasks = []
    for i in range(n):
        if i % 3 == 0:
            tasks.append(
                send(
                    client,
                    "POST",
                    "/users",
                    stats.name,
                    json={
                        "name": f"pool_{RUN_ID}_{i}",
                        "email": f"pool_{RUN_ID}_{i}@test.com",
                    },
                )
            )
        elif i % 3 == 1:
            tasks.append(send(client, "GET", "/todos", stats.name))
        else:
            tasks.append(send(client, "GET", "/users", stats.name))

    results = await asyncio.gather(*tasks)
    for r in results:
        stats.add(r)


# ---------------------------------------------------------------------------
# 시나리오 5: 연속 트랜잭션 경합 (단일 리소스 집중 수정)
# ---------------------------------------------------------------------------


async def scenario_contention(
    client: httpx.AsyncClient,
    stats: ScenarioStats,
    target_user_id: int,
    concurrency: int,
) -> None:
    """동일한 user_id를 동시에 UPDATE → 쓰기 경합 극대화"""
    print(
        f"\n  ⚡ 쓰기 경합 테스트: user_id={target_user_id}에 {concurrency}개 동시 PUT"
    )

    sem = asyncio.Semaphore(concurrency)

    async def update(i: int) -> None:
        async with sem:
            r = await send(
                client,
                "PUT",
                f"/users/{target_user_id}",
                stats.name,
                json={"name": f"contended_{i}", "email": f"contended_{i}@test.com"},
            )
            stats.add(r)

    await asyncio.gather(*[update(i) for i in range(concurrency * 2)])


# ---------------------------------------------------------------------------
# 서버 헬스체크
# ---------------------------------------------------------------------------


async def check_server(client: httpx.AsyncClient) -> bool:
    try:
        resp = await client.get(f"{BASE_URL}/users", timeout=3.0)
        return resp.status_code < 500
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 준비: 테스트용 유저/태그/투두 생성
# ---------------------------------------------------------------------------


async def setup_fixtures(client: httpx.AsyncClient) -> dict[str, int]:
    """테스트에 필요한 초기 데이터 생성, 이미 있으면 재사용"""
    # user
    r = await client.post(
        f"{BASE_URL}/users",
        json={"name": f"fixture_{RUN_ID}", "email": f"fixture_{RUN_ID}@stress.test"},
    )
    if r.status_code == 201:
        user_id = r.json()["id"]
    else:
        users = await client.get(f"{BASE_URL}/users")
        user_id = users.json()[0]["id"] if users.json() else 1

    # tag
    r = await client.post(f"{BASE_URL}/tags", json={"name": f"stress-tag-{RUN_ID}"})
    tag_id = r.json()["id"] if r.status_code == 201 else 1

    # todo
    r = await client.post(
        f"{BASE_URL}/todos", json={"title": "fixture todo", "assignee_id": user_id}
    )
    todo_id = r.json()["id"] if r.status_code == 201 else 1

    return {"user_id": user_id, "tag_id": tag_id, "todo_id": todo_id}


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


async def main(concurrency: int, total_requests: int) -> None:
    print("=" * 60)
    print("  Team-Todo API — 동시 접속 / DB 커넥션 풀 스트레스 테스트")
    print("=" * 60)
    print(f"  대상 서버  : {BASE_URL}")
    print(f"  동시성     : {concurrency}")
    print(f"  총 요청수  : {total_requests} (시나리오별)")

    limits = httpx.Limits(
        max_connections=concurrency + 20,
        max_keepalive_connections=concurrency,
    )
    timeout = httpx.Timeout(30.0, connect=5.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        # 서버 확인
        if not await check_server(client):
            print("\n❌ 서버에 접속할 수 없습니다. 먼저 서버를 실행하세요:")
            print("   uv run uvicorn app.main:app --reload")
            return

        print("\n✅ 서버 정상 확인\n")

        # 픽스처 준비
        fixtures = await setup_fixtures(client)
        print(f"  픽스처 준비 완료: {fixtures}")

        sem = asyncio.Semaphore(concurrency)
        all_stats: list[ScenarioStats] = []

        # ── 시나리오 1: 읽기 부하 ──────────────────────────────────
        print(f"\n[1/5] 순수 읽기 부하  ({total_requests} req, 동시성 {concurrency})")
        s1 = ScenarioStats("1. 순수 읽기 (GET)")
        t0 = time.perf_counter()
        await scenario_read_load(client, s1, total_requests, sem)
        elapsed = time.perf_counter() - t0
        print(f"     완료 — {elapsed:.2f}초, {total_requests / elapsed:.1f} req/s")
        all_stats.append(s1)

        # ── 시나리오 2: 쓰기 부하 ──────────────────────────────────
        print(f"\n[2/5] 순수 쓰기 부하  ({total_requests} req, 동시성 {concurrency})")
        s2 = ScenarioStats("2. 순수 쓰기 (POST)")
        t0 = time.perf_counter()
        await scenario_write_load(client, s2, total_requests, sem)
        elapsed = time.perf_counter() - t0
        print(f"     완료 — {elapsed:.2f}초, {total_requests / elapsed:.1f} req/s")
        all_stats.append(s2)

        # ── 시나리오 3: 혼합 부하 ──────────────────────────────────
        print(
            f"\n[3/5] 혼합 부하 70R/30W  ({total_requests} req, 동시성 {concurrency})"
        )
        s3 = ScenarioStats("3. 혼합 (GET 70% / POST 30%)")
        t0 = time.perf_counter()
        await scenario_mixed_load(client, s3, total_requests, sem)
        elapsed = time.perf_counter() - t0
        print(f"     완료 — {elapsed:.2f}초, {total_requests / elapsed:.1f} req/s")
        all_stats.append(s3)

        # ── 시나리오 4: 커넥션 풀 포화 ────────────────────────────
        pool_n = min(total_requests, 200)  # 너무 많으면 OS 소켓 한계 도달
        print(f"\n[4/5] 커넥션 풀 포화  ({pool_n} req 동시 발사)")
        s4 = ScenarioStats("4. 커넥션 풀 포화 (동시 발사)")
        t0 = time.perf_counter()
        await scenario_pool_exhaustion(client, s4, pool_n, concurrency)
        elapsed = time.perf_counter() - t0
        print(f"     완료 — {elapsed:.2f}초, {pool_n / elapsed:.1f} req/s")
        all_stats.append(s4)

        # ── 시나리오 5: 단일 리소스 쓰기 경합 ────────────────────
        user_id = fixtures["user_id"]
        print(f"\n[5/5] 쓰기 경합  (user_id={user_id}에 {concurrency * 2}개 동시 PUT)")
        s5 = ScenarioStats("5. 단일 리소스 쓰기 경합 (PUT)")
        t0 = time.perf_counter()
        await scenario_contention(client, s5, user_id, concurrency)
        elapsed = time.perf_counter() - t0
        print(f"     완료 — {elapsed:.2f}초")
        all_stats.append(s5)

        # ── 최종 리포트 ─────────────────────────────────────────
        print("\n\n" + "=" * 60)
        print("  최종 결과 리포트")
        print("=" * 60)
        for s in all_stats:
            s.print_summary()

        # 전체 요약
        total_reqs = sum(s.total for s in all_stats)
        total_errors = sum(s.errors for s in all_stats)
        all_lats = [lat for s in all_stats for lat in s.latencies]
        print(f"\n{'=' * 60}")
        print("  전체 요약")
        print(f"{'=' * 60}")
        print(f"  총 요청수   : {total_reqs}")
        print(
            f"  총 실패수   : {total_errors}  ({total_errors / total_reqs * 100:.1f}%)"
        )
        if all_lats:
            print(f"  전체 평균   : {statistics.mean(all_lats):.1f} ms")
            lats_sorted = sorted(all_lats)
            p95 = lats_sorted[int(len(lats_sorted) * 0.95)]
            p99 = lats_sorted[int(len(lats_sorted) * 0.99)]
            print(f"  전체 P95    : {p95:.1f} ms")
            print(f"  전체 P99    : {p99:.1f} ms")

        # DB 커넥션 풀 진단
        print(f"\n{'─' * 60}")
        print("  DB 커넥션 풀 진단")
        print(f"{'─' * 60}")
        pool_error_rate = s4.error_rate
        write_error_rate = s2.error_rate
        contention_error_rate = s5.error_rate

        if pool_error_rate > 5 or write_error_rate > 5:
            print("  ⚠️  쓰기/풀 포화 시 오류율이 높습니다.")
            print("     → pool_size, max_overflow, pool_timeout 조정 필요")
            print("     → SQLite 대신 PostgreSQL 전환 검토")
        else:
            print("  ✅ 커넥션 풀이 현재 부하를 잘 처리했습니다.")

        if contention_error_rate > 10:
            print("  ⚠️  동일 리소스 동시 쓰기 경합이 심각합니다.")
            print("     → 낙관적 잠금(Optimistic Lock) 또는 Retry 로직 필요")
        else:
            print("  ✅ 쓰기 경합이 허용 범위 내입니다.")

        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Team-Todo 스트레스 테스트")
    parser.add_argument(
        "--concurrency", type=int, default=20, help="동시 요청 수 (기본: 20)"
    )
    parser.add_argument(
        "--requests", type=int, default=200, help="시나리오당 총 요청 수 (기본: 200)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(concurrency=args.concurrency, total_requests=args.requests))
