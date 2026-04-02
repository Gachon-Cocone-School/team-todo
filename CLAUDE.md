# CLAUDE.md

## 프로젝트 개요

팀 멤버가 함께 사용하는 Todo 관리 백엔드 API.
Python FastAPI + SQLite 기반, 인증 없음.

## 기술 스택

- **언어/프레임워크**: Python 3.11+ / FastAPI
- **DB**: SQLite (SQLAlchemy ORM)
- **마이그레이션**: Alembic
- **패키지 관리**: uv

## 패키지 관리 규칙

이 프로젝트는 **uv**를 사용한다. pip, pip-tools, poetry는 사용하지 않는다.

```bash
# 의존성 설치
uv sync

# 패키지 추가
uv add <package>

# 명령 실행
uv run <command>
```

## 커밋 전 자동 검사 순서

커밋 시 pre-commit이 아래 순서로 강제 실행된다. 모두 통과해야 커밋된다.

| 단계 | 도구 | 목적 |
|------|------|------|
| 1 | `ruff check --fix` | 린트 오류 자동 수정 |
| 2 | `ruff format` | 코드 포맷 통일 |
| 3 | `mypy app/` | 정적 타입 검사 |
| 4 | `pytest tests/` | 테스트 통과 확인 |
| 5 | `pylint app/` | **코드 중복 감지** (테스트 통과 후) |

```bash
# 수동 실행
uv run ruff check --fix .    # 린트
uv run ruff format .         # 포맷
uv run mypy app/             # 타입 검사
uv run pytest tests/         # 테스트
uv run pylint app/           # 중복 코드 검사
```

## 코드 품질 규칙

- `print()` 사용 금지 (T20) — 로깅 사용
- 모든 함수에 타입 힌트 필수 (ANN)
- 주석 처리된 코드 금지 (ERA)
- timezone-naive datetime 금지 (DTZ)
- 함수 복잡도(McCabe) 10 초과 금지 (C90) → **리팩토링 필수**
- 함수 인자 최대 7개 (PLR) → 초과 시 객체로 묶기
- **6줄 이상 중복 코드 금지** (pylint R0801) → **공통 함수/모듈로 추출**

## 서버 실행

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# API 문서: http://localhost:8000/docs
```

## 코드 구조

```
app/
├── main.py        # FastAPI 앱 진입점
├── database.py    # SQLAlchemy 엔진/세션
├── models/        # ORM 모델
├── schemas/       # Pydantic 스키마
├── routers/       # API 라우터
└── crud/          # DB 조작 로직
```

## 참고 문서

- [PRD](docs/PRD.md) - 기능 요구사항 및 API 엔드포인트
- [TSD](docs/TSD.md) - 기술 명세 및 레이어 구조
- [DATABASE](docs/DATABASE.md) - DB 테이블 설계 및 ERD
