# 성능 감사 보고서 (Performance Audit Report)

**프로젝트**: Team Todo API  
**감사일**: 2026-04-02  
**감사 범위**: `app/` 전체 소스코드 + 동시 접속 스트레스 테스트  
**테스트 환경**: macOS (Apple Silicon), SQLite 파일 DB, uvicorn 단일 워커

---

## 1. 스트레스 테스트 결과

### 1-1. 테스트 방법

`tests/stress_test.py` (asyncio + httpx)로 5가지 시나리오를 3개 부하 단계에 걸쳐 측정했다.

| 시나리오 | 설명 |
|----------|------|
| 순수 읽기 | `GET /todos`, `GET /users`, `GET /tags` 균등 분배 |
| 순수 쓰기 | `POST /users` (고유 이메일) |
| 혼합 | GET 70% / POST 30% |
| 커넥션 풀 포화 | 세마포어 없이 전량 동시 발사 |
| 쓰기 경합 | 동일 리소스(`PUT /users/{id}`)에 최대 동시성 집중 |

---

### 1-2. 저부하 결과 (동시성 20, 시나리오당 200 req)

| 시나리오 | req/s | 평균 (ms) | P95 (ms) | P99 (ms) | 오류율 |
|----------|-------|-----------|----------|----------|--------|
| 순수 읽기 | **386** | 49 | 119 | 190 | 0% |
| 순수 쓰기 | 268 | 70 | 159 | 295 | 0% |
| 혼합 70R/30W | 314 | 52 | 216 | 345 | 0% |
| 커넥션 풀 포화 | 260 | 372 | 660 | 751 | 0% |
| 쓰기 경합 (40req) | — | 77 | 175 | 177 | 0% |

**판정**: 동시성 20 이하에서는 정상 동작. 쓰기가 읽기 대비 약 30% 느림.

---

### 1-3. 중부하 결과 (동시성 50, 시나리오당 500 req)

| 시나리오 | req/s | 평균 (ms) | P95 (ms) | P99 (ms) | 오류율 |
|----------|-------|-----------|----------|----------|--------|
| 순수 읽기 | 60 | **786** | 1,470 | 1,707 | 0% |
| 순수 쓰기 | 111 | 430 | 1,305 | 1,735 | 0% |
| 혼합 70R/30W | 121 | 387 | 848 | 1,200 | 0% |
| 커넥션 풀 포화 (200req) | 86 | **1,192** | 2,070 | 2,179 | 0% |
| 쓰기 경합 (100req) | — | 367 | 814 | 835 | 1% |

**판정**: 오류 없이 처리하지만 읽기 P99가 **1.7초**, 풀 포화 평균이 **1.2초**로 체감 지연 시작.

> ⚠️ 읽기가 쓰기보다 느린 역전 현상: SQLite Single-Writer Lock으로 인해 쓰기가 직렬화되는 반면, 읽기는 50개 동시 커넥션이 경합하며 레이턴시가 급등함.

---

### 1-4. 고부하 결과 (동시성 100, 시나리오당 1000 req)

| 시나리오 | req/s | 오류율 | 주요 오류 |
|----------|-------|--------|----------|
| 순수 읽기 | 182 | **0%** | — |
| 순수 쓰기 | 353 | 20% | HTTP 400 (이메일 중복 — 재실행 데이터) |
| 혼합 70R/30W | 11 | 26% | HTTP 400, 타임아웃 |
| 커넥션 풀 포화 (200req) | — | **100%** | 타임아웃 (30s 초과) |
| 쓰기 경합 (200req) | — | **100%** | 타임아웃 (60s 초과) |

**판정**: 동시성 100에서 풀 포화·쓰기 경합 시나리오 완전 실패. SQLite 단일 쓰기 락이 병목.

---

### 1-5. 처리량 한계 요약

```
읽기 처리 한계: 동시성 ~50 (P99 < 2s 기준)
쓰기 처리 한계: 동시성 ~30 (P99 < 1.5s 기준)
완전 장애 임계: 동시성 100 이상 + 집중 쓰기
```

---

## 2. 코드 레벨 성능 문제

### PERF-001 · N+1 쿼리 위험 — `get_todos()`의 태그 지연 로딩

| 항목 | 내용 |
|------|------|
| 파일 | `app/crud/todo.py:12-30` |
| 심각도 | 🟠 High |

**현황**  
`get_todos()`는 `selectinload` 없이 Todo를 조회한다. 응답 시 Pydantic이 `tags` 필드를 직렬화하면 **Todo당 별도 SELECT** 가 발생한다. 100개 Todo라면 101번 쿼리.

```python
def get_todos(db: Session, ...) -> list[Todo]:
    stmt = select(Todo)
    ...
    return list(db.execute(stmt).scalars().all())  # ← selectinload(Todo.tags) 없음
```

반면 단건 조회는 올바르게 처리된다:
```python
def get_todo(db: Session, todo_id: int) -> Todo | None:
    return db.execute(
        select(Todo).where(Todo.id == todo_id).options(selectinload(Todo.tags))  # ← 올바름
    ).scalar_one_or_none()
```

**권고 조치**
```python
def get_todos(db: Session, ...) -> list[Todo]:
    stmt = select(Todo).options(selectinload(Todo.tags))
    ...
```

---

### PERF-002 · DB 인덱스 부재 (Missing Indexes)

| 항목 | 내용 |
|------|------|
| 파일 | `app/models/` 전체, `alembic/` 마이그레이션 |
| 심각도 | 🟠 High |

**현황**  
PK와 UNIQUE 컬럼 외에 자주 필터링되는 컬럼에 인덱스가 없다.

| 컬럼 | 사용 패턴 | 인덱스 여부 |
|------|-----------|------------|
| `todos.assignee_id` | `WHERE assignee_id = ?` | FK만 있음, **인덱스 없음** |
| `todos.status` | `WHERE status = ?` | **없음** |
| `todos.priority` | `WHERE priority = ?` | **없음** |
| `todos.created_by` | FK 참조 | FK만 있음, **인덱스 없음** |
| `comments.todo_id` | `WHERE todo_id = ?` | FK만 있음, **인덱스 없음** |
| `comments.author_id` | FK 참조 | FK만 있음, **인덱스 없음** |

SQLite는 FK 컬럼에 자동 인덱스를 생성하지 않는다.

**권고 조치** (Alembic 마이그레이션 추가)
```python
op.create_index("ix_todos_assignee_id", "todos", ["assignee_id"])
op.create_index("ix_todos_status", "todos", ["status"])
op.create_index("ix_todos_priority", "todos", ["priority"])
op.create_index("ix_todos_created_by", "todos", ["created_by"])
op.create_index("ix_comments_todo_id", "comments", ["todo_id"])
```

---

### PERF-003 · 페이지네이션 없음 (No Pagination)

| 항목 | 내용 |
|------|------|
| 파일 | `app/crud/user.py:10`, `app/crud/todo.py:12`, `app/crud/tag.py:10` |
| 심각도 | 🟠 High |

**현황**  
모든 목록 조회가 `LIMIT` 없이 전체 행을 반환한다. 10만 건 Todo가 있다면 `/todos` 호출 한 번이 메모리 폭증과 응답 지연을 유발한다.

```python
def get_users(db: Session) -> list[User]:
    return list(db.execute(select(User)).scalars().all())  # ← 전체 반환
```

**권고 조치**
```python
@router.get("", response_model=list[UserResponse])
def list_users(skip: int = 0, limit: int = Query(default=50, le=200), db: Session = Depends(get_db)):
    return crud.user.get_users(db, skip=skip, limit=limit)
```

---

### PERF-004 · DB 커넥션 풀 미설정 (No Connection Pool Configuration)

| 항목 | 내용 |
|------|------|
| 파일 | `app/database.py:11` |
| 심각도 | 🟡 Medium |

**현황**  
`pool_size`, `max_overflow`, `pool_timeout`, `pool_pre_ping` 없이 SQLAlchemy 기본값을 사용한다. SQLite 파일 DB에서 SQLAlchemy 기본 풀은 `SingletonThreadPool`로 **스레드당 1개 커넥션**을 할당한다.

```python
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# pool_size, max_overflow, pool_timeout 미설정
```

스트레스 테스트 결과:
- 동시성 100에서 풀 포화 시나리오 **100% 타임아웃**
- 쓰기 경합 시나리오 **100% 타임아웃** (60초 초과)

**권고 조치**
```python
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,          # SQLite 락 대기 시간
    },
    pool_pre_ping=True,         # 스테일 커넥션 자동 감지
    pool_size=10,               # 기본 커넥션 수
    max_overflow=20,            # 최대 추가 커넥션
    pool_timeout=30,            # 풀 고갈 시 대기 시간
)
```

---

### PERF-005 · SQLite WAL 모드 미적용

| 항목 | 내용 |
|------|------|
| 파일 | `app/database.py:21-25` |
| 심각도 | 🟡 Medium |

**현황**  
`PRAGMA foreign_keys=ON`만 설정되어 있다. SQLite 기본 저널 모드(DELETE)는 **쓰기 시 전체 DB 파일 잠금**이 발생해 읽기도 블록된다.

**권고 조치**
```python
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")     # 읽기/쓰기 동시 허용
    cursor.execute("PRAGMA busy_timeout=5000")    # 락 대기 5초
    cursor.execute("PRAGMA synchronous=NORMAL")   # WAL 모드 최적화
    cursor.close()
```

WAL 모드 적용 시 읽기와 쓰기가 동시에 가능해 중부하에서 읽기 P99가 약 **40~60% 개선** 예상.

---

### PERF-006 · 동기 DB 세션 (Sync SQLAlchemy in Async FastAPI)

| 항목 | 내용 |
|------|------|
| 파일 | `app/database.py`, `app/routers/` 전체 |
| 심각도 | 🟡 Medium |

**현황**  
FastAPI는 asyncio 기반이지만 `sessionmaker` + 동기 `Session`을 사용한다. Uvicorn이 동기 라우터 함수를 스레드풀(`run_in_executor`)로 실행하므로 스레드 수 = 동시 처리 가능 요청 수가 된다.

```python
# 동기 세션 — 스레드풀 실행
SessionLocal: sessionmaker[Session] = sessionmaker(...)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    ...
```

**권고 조치** (장기)  
PostgreSQL + `asyncpg` + `AsyncSession`으로 전환하면 스레드 오버헤드 없이 수백 개 동시 연결 처리 가능.

```python
# 비동기 세션 예시
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine("postgresql+asyncpg://...")
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)
```

---

### PERF-007 · 매 쓰기마다 `db.refresh()` 호출

| 항목 | 내용 |
|------|------|
| 파일 | `app/crud/` 전체 (create_*, update_* 함수) |
| 심각도 | 🔵 Low |

**현황**  
모든 생성·수정 함수가 `db.commit()` 직후 `db.refresh()`를 호출해 **추가 SELECT**를 실행한다. 단건 처리에서는 영향이 작지만 bulk 처리 시 비효율적이다.

```python
db.add(user)
db.commit()
db.refresh(user)  # ← 추가 SELECT
return user
```

**권고 조치**  
`server_default`로 설정된 `created_at` 같은 필드만 refresh가 필요하다. `expire_on_commit=False` 옵션으로 일부 케이스에서 refresh를 생략할 수 있다.

---

## 3. 성능 개선 로드맵

### 단기 (코드 변경, 1~2일)

| 우선순위 | 항목 | 예상 개선 효과 |
|----------|------|----------------|
| 1 | PERF-001 `selectinload` 추가 | N+1 제거, 읽기 쿼리 수 대폭 감소 |
| 2 | PERF-005 WAL 모드 + busy_timeout | 읽기 P99 40~60% 개선 예상 |
| 3 | PERF-004 pool 설정 | 고부하 타임아웃 방지 |

### 중기 (아키텍처 변경, 1~2주)

| 우선순위 | 항목 | 예상 개선 효과 |
|----------|------|----------------|
| 4 | PERF-002 인덱스 추가 | 필터링 쿼리 O(n) → O(log n) |
| 5 | PERF-003 페이지네이션 | 메모리 안정성 확보 |

### 장기 (인프라 전환, 1개월 이상)

| 우선순위 | 항목 | 예상 개선 효과 |
|----------|------|----------------|
| 6 | PostgreSQL + asyncpg 전환 | 동시성 수백 수준으로 확장 |
| 7 | 읽기 캐시 도입 (Redis) | 자주 조회되는 목록 응답 ms 단위 |

---

## 4. 현재 성능 수용 가이드

| 사용 시나리오 | 판정 |
|--------------|------|
| 팀 내 소규모 사용 (동시 접속 < 10) | ✅ 충분 |
| 팀 전체 사용 (동시 접속 10~30) | ✅ 정상 (P99 < 350ms) |
| 중규모 서비스 (동시 접속 30~50) | ⚠️ 읽기 P99 1.5초 초과, WAL 적용 필요 |
| 대규모 서비스 (동시 접속 50+) | ❌ PostgreSQL 전환 필수 |
