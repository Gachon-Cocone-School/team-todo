# TSD: 팀 Todo 앱 백엔드 기술 명세

## 프로젝트 구조

```
team-todo/
├── app/
│   ├── main.py              # FastAPI 앱 진입점, 라우터 등록
│   ├── database.py          # SQLAlchemy 엔진, 세션, Base
│   ├── models/              # SQLAlchemy ORM 모델
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── todo.py
│   │   ├── comment.py
│   │   └── tag.py
│   ├── schemas/             # Pydantic 요청/응답 스키마
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── todo.py
│   │   ├── comment.py
│   │   └── tag.py
│   ├── routers/             # API 라우터
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── todos.py
│   │   ├── comments.py
│   │   └── tags.py
│   └── crud/                # DB 조작 로직
│       ├── __init__.py
│       ├── user.py
│       ├── todo.py
│       ├── comment.py
│       └── tag.py
├── alembic/                 # DB 마이그레이션
│   ├── versions/
│   └── env.py
├── alembic.ini
├── pyproject.toml           # 프로젝트 메타데이터 및 의존성 (uv 관리)
├── uv.lock                  # 의존성 잠금 파일
├── docs/
│   ├── PRD.md
│   ├── TSD.md
│   └── DATABASE.md
└── CLAUDE.md
```

## 패키지 관리 (uv)

[uv](https://docs.astral.sh/uv/)를 사용하여 Python 버전 및 의존성을 관리한다.  
의존성은 `pyproject.toml`에 선언하고 `uv.lock`으로 버전을 고정한다.

```toml
# pyproject.toml
[project]
requires-python = ">=3.11"
dependencies = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "alembic",
]
```

### 주요 uv 명령어

```bash
# 의존성 설치 (가상환경 자동 생성)
uv sync

# 패키지 추가
uv add <package>

# 패키지 제거
uv remove <package>

# 명령 실행 (가상환경 자동 활성화)
uv run <command>
```

## 실행 방법

```bash
# 의존성 설치
uv sync

# DB 마이그레이션
uv run alembic upgrade head

# 서버 실행
uv run uvicorn app.main:app --reload

# API 문서 확인
# http://localhost:8000/docs
```

## 레이어 구조

```
Router (HTTP 요청/응답)
  └── CRUD (DB 조작)
        └── Model (SQLAlchemy ORM)
              └── SQLite DB
```

- **Router**: 요청 수신, 스키마 검증, CRUD 호출, 응답 반환
- **CRUD**: 비즈니스 로직 없이 순수 DB 조작만 담당
- **Schema**: 요청/응답 데이터 형식 정의 (Pydantic)
- **Model**: 테이블 정의 (SQLAlchemy)

## Enum 정의

```python
class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
```

## 필터링 쿼리 파라미터 (GET /todos)

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `status` | string | todo / in_progress / done |
| `priority` | string | low / medium / high |
| `assignee_id` | int | 담당자 ID |
| `tag_id` | int | 태그 ID |

## 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

주요 HTTP 상태 코드:
- `200` OK
- `201` Created
- `404` Not Found
- `422` Validation Error

## 린팅 & 타입 검사

### 도구

| 도구 | 역할 |
|------|------|
| `ruff` | 린터 + 포매터 (pycodestyle, pyflakes, isort 등 통합) |
| `mypy` | 정적 타입 검사 |

### 주요 명령어

```bash
# 린트 검사
uv run ruff check .

# 린트 자동 수정
uv run ruff check --fix .

# 코드 포맷
uv run ruff format .

# 타입 검사
uv run mypy app/
```

### 활성화된 주요 Ruff 규칙

| 코드 | 설명 |
|------|------|
| E/W | pycodestyle 오류/경고 |
| F | pyflakes (미사용 임포트 등) |
| I | isort (임포트 정렬) |
| N | pep8-naming (네이밍 컨벤션) |
| UP | pyupgrade (최신 Python 문법 강제) |
| B | flake8-bugbear (잠재적 버그) |
| ANN | flake8-annotations (타입 힌트 강제) |
| S | flake8-bandit (보안 취약점) |
| T20 | print 문 금지 |
| ERA | 주석 처리된 코드 금지 |
| DTZ | timezone-aware datetime 강제 |
| PL | pylint 규칙 |
| PERF | 성능 안티패턴 |
| FURB | 관용적 Python 패턴 |

## 구현 순서

1. 프로젝트 세팅 (폴더 구조, uv 환경 초기화)
2. `database.py` - SQLAlchemy 엔진/세션 설정
3. `models/` - ORM 모델 정의
4. Alembic 초기화 및 마이그레이션
5. `schemas/` - Pydantic 스키마 정의
6. `crud/` - CRUD 함수 구현
7. `routers/` - 라우터 구현 (Users → Todos → Comments → Tags)
8. `main.py` - 라우터 등록 및 앱 설정
