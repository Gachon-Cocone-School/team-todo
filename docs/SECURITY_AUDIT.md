# 보안 감사 보고서 (Security Audit Report)

**프로젝트**: Team Todo API  
**감사일**: 2026-04-02  
**감사 범위**: `app/` 전체 소스코드 (routers, crud, models, schemas, database)  
**도구**: ruff (flake8-bandit S 규칙), mypy strict, 수동 코드 리뷰

---

## 요약

| 심각도 | 건수 |
|--------|------|
| 🔴 Critical | 2 |
| 🟠 High | 4 |
| 🟡 Medium | 4 |
| 🔵 Low | 3 |
| **합계** | **13** |

정적 분석(ruff, mypy) 결과는 **모두 통과**. 아래 항목은 코드 로직 및 설계 수준의 취약점으로, 자동화 도구로는 검출되지 않는 구조적 문제들이다.

---

## 🔴 Critical

### SEC-001 · 인증/인가 전무 (No Authentication / Authorization)

| 항목 | 내용 |
|------|------|
| 파일 | `app/main.py`, 모든 라우터 |
| 관련 OWASP | A01:2021 – Broken Access Control |

**현황**  
모든 엔드포인트에 인증 미들웨어가 없다. 누구든지 다음 작업이 가능하다:
- 타인의 Todo/댓글 수정 및 삭제
- 모든 유저 목록·상세 조회
- 임의 유저 생성·삭제

**근거 코드** (`app/main.py`)
```python
app = FastAPI(title="Team Todo API", version="0.1.0")
# CORSMiddleware, APIKeyMiddleware, OAuth2 등 없음
```

**위험**: 인터넷에 노출 시 데이터 전체 탈취·파괴 가능.

**권고 조치**
```python
# 최소 API Key 인증 예시
from fastapi.security import APIKeyHeader
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(key: str = Depends(api_key_header)):
    if key != settings.API_KEY:
        raise HTTPException(403)
```
장기적으로는 JWT + OAuth2 Password Flow 도입을 권장한다.

---

### SEC-002 · 클라이언트 공급 신원 (Identity Spoofing via `created_by` / `author_id`)

| 항목 | 내용 |
|------|------|
| 파일 | `app/schemas/todo.py:17`, `app/schemas/comment.py:9` |
| 관련 OWASP | A01:2021 – Broken Access Control |

**현황**  
Todo 생성 시 `created_by`, 댓글 생성 시 `author_id`를 **클라이언트 요청 바디**에서 받는다. 인증이 없으므로 누구나 타인의 ID를 사칭할 수 있다.

**근거 코드**
```python
# app/schemas/todo.py
class TodoCreate(BaseModel):
    title: str
    created_by: int  # ← 클라이언트 임의 지정 가능

# app/schemas/comment.py
class CommentCreate(BaseModel):
    author_id: int  # ← 클라이언트 임의 지정 가능
    content: str
```

**위험**: Alice가 Bob의 `user_id`를 넣어 Bob 명의로 Todo·댓글 생성 가능.

**권고 조치**  
인증 도입 후 서버 측에서 현재 세션 유저 ID를 주입해야 한다.
```python
# created_by를 스키마에서 제거하고 라우터에서 주입
def create_todo(data: TodoCreate, current_user: User = Depends(get_current_user)):
    return crud.todo.create_todo(db, data, creator_id=current_user.id)
```

---

## 🟠 High

### SEC-003 · 이메일 형식 미검증 (No Email Format Validation)

| 항목 | 내용 |
|------|------|
| 파일 | `app/schemas/user.py:9` |
| 관련 OWASP | A03:2021 – Injection |

**현황**  
`UserCreate.email`이 단순 `str`로 선언되어 있어 형식 검증이 없다. `"not-an-email"`, `"<script>alert(1)</script>"` 등이 그대로 저장된다.

```python
class UserCreate(BaseModel):
    name: str
    email: str  # ← EmailStr 또는 field_validator 없음
```

**권고 조치**
```python
from pydantic import EmailStr

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
```

---

### SEC-004 · 입력 길이 미검증 (No Input Length Limits in Schemas)

| 항목 | 내용 |
|------|------|
| 파일 | `app/schemas/` 전체 |
| 관련 OWASP | A03:2021 – Injection |

**현황**  
DB 모델에는 `String(100)`, `String(255)`, `String(50)` 등 컬럼 길이가 정의되어 있지만, Pydantic 스키마에는 길이 제한이 없다. 아래 조합이 모두 가능하다:

| 스키마 필드 | DB 제한 | 스키마 제한 |
|-------------|---------|------------|
| `User.name` | 100자 | **없음** |
| `User.email` | 255자 | **없음** |
| `Todo.title` | 255자 | **없음** |
| `Tag.name` | 50자 | **없음** |
| `Tag.color` | 7자 | **없음** |
| `Comment.content` | Text(무제한) | **없음** |

특히 `Comment.content`는 DB 컬럼이 `Text`이므로 수십 MB 페이로드가 그대로 저장된다.

**권고 조치**
```python
from pydantic import Field

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr

class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
```

---

### SEC-005 · 속도 제한 없음 (No Rate Limiting)

| 항목 | 내용 |
|------|------|
| 파일 | `app/main.py` |
| 관련 OWASP | A05:2021 – Security Misconfiguration |

**현황**  
요청 속도 제한이 없어 단일 IP에서 무제한 요청이 가능하다. 스트레스 테스트 결과, 동시성 20에서 **386 req/s** 처리가 가능하므로 서비스 방해 공격이 용이하다.

**권고 조치**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/users")
@limiter.limit("10/minute")
def create_user(...):
    ...
```

---

### SEC-006 · 페이지네이션 없음 — 데이터 전체 노출 (No Pagination)

| 항목 | 내용 |
|------|------|
| 파일 | `app/routers/todos.py:14`, `app/routers/users.py:14`, `app/routers/tags.py:14` |
| 관련 OWASP | A01:2021 – Broken Access Control |

**현황**  
모든 목록 조회 엔드포인트가 `LIMIT` 없이 전체 데이터를 반환한다. 인증이 없으므로 `/users`만 호출해도 전체 유저의 이름·이메일을 일괄 수집할 수 있다.

```python
def get_users(db: Session) -> list[User]:
    return list(db.execute(select(User)).scalars().all())  # ← LIMIT 없음
```

**권고 조치**
```python
def get_users(db: Session, skip: int = 0, limit: int = 50) -> list[User]:
    return list(db.execute(select(User).offset(skip).limit(limit)).scalars().all())
```

---

## 🟡 Medium

### SEC-007 · TOCTOU 경쟁 조건 (Check-Then-Insert Race Condition)

| 항목 | 내용 |
|------|------|
| 파일 | `app/crud/user.py:19-28`, `app/crud/tag.py:18-26` |
| 관련 OWASP | A04:2021 – Insecure Design |

**현황**  
이메일 중복 체크와 INSERT 사이에 트랜잭션 격리가 없다. 두 요청이 동시에 동일 이메일로 도달하면 둘 다 체크를 통과한 뒤 하나가 DB 유니크 제약으로 실패하지만, **오류 처리가 없어 500 에러로 노출**된다.

```python
def create_user(db: Session, data: UserCreate) -> User:
    existing = db.execute(...)  # 1) 체크
    if existing is not None:
        raise ValueError("Email already exists")
    user = User(...)
    db.add(user)
    db.commit()              # 2) INSERT — 1)과 2) 사이 race 발생 가능
```

스트레스 테스트(동시성 100)에서 실제로 **HTTP 400 오류가 발생**함을 확인했다.

**권고 조치**  
DB 유니크 제약 위반(`IntegrityError`)을 CRUD 레이어에서 명시적으로 처리한다.
```python
from sqlalchemy.exc import IntegrityError

try:
    db.commit()
except IntegrityError:
    db.rollback()
    raise ValueError("Email already exists")
```

---

### SEC-008 · 오류 메시지 정보 노출 (Error Message Information Leakage)

| 항목 | 내용 |
|------|------|
| 파일 | `app/routers/` 전체 |
| 관련 OWASP | A05:2021 – Security Misconfiguration |

**현황**  
CRUD 레이어의 `ValueError` 메시지가 그대로 HTTP 응답 바디에 노출된다.

```python
# app/routers/users.py
except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
    # → {"detail": "Email already exists"} — 내부 로직 노출
```

DB 스키마 구조, 비즈니스 규칙을 외부에서 파악할 수 있다.

**권고 조치**  
에러 코드 기반의 표준 응답으로 추상화한다.
```python
raise HTTPException(status_code=400, detail="USER_EMAIL_DUPLICATE")
```

---

### SEC-009 · 하드코딩된 DB 경로 (Hardcoded Database URL)

| 항목 | 내용 |
|------|------|
| 파일 | `app/database.py:9` |
| 관련 OWASP | A02:2021 – Cryptographic Failures |

**현황**
```python
DATABASE_URL = "sqlite:///./todo.db"  # 하드코딩
```

환경별(개발/스테이징/운영) 분리가 불가능하고, 운영 DB 경로가 코드에 노출된다.

**권고 조치**
```python
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./todo.db")
```

---

### SEC-010 · CORS 설정 없음 (No CORS Policy)

| 항목 | 내용 |
|------|------|
| 파일 | `app/main.py` |
| 관련 OWASP | A05:2021 – Security Misconfiguration |

**현황**  
`CORSMiddleware`가 설정되지 않아 FastAPI 기본값(모든 오리진 허용)이 적용된다. 악의적인 웹사이트에서 피해자 브라우저를 통해 API를 호출할 수 있다.

**권고 조치**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## 🔵 Low

### SEC-011 · HTTPS 미적용 (No HTTPS Enforcement)

서버가 HTTP로만 제공되어 네트워크 도청이 가능하다. 운영 환경에서는 Nginx/Caddy 등 리버스 프록시를 통해 TLS를 종료해야 한다.

---

### SEC-012 · 감사 로그 없음 (No Audit Logging)

생성·수정·삭제 작업에 대한 로그가 없어 사고 발생 시 원인 추적이 불가능하다. `who did what when`을 기록하는 감사 로그 미들웨어 도입을 권장한다.

---

### SEC-013 · Tag color 형식 미검증

`Tag.color`가 `String(7)`로 선언되어 있으나 스키마에서 hex 색상 형식(`#RRGGBB`) 검증이 없다.
```python
# 권고
from pydantic import Field
color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
```

---

## 우선순위 조치 로드맵

| 순위 | 항목 | 예상 공수 | 효과 |
|------|------|-----------|------|
| 1 | SEC-001 인증/인가 도입 | 大 | 나머지 절반 해결 |
| 2 | SEC-003, SEC-004 입력 검증 강화 | 小 | 즉시 적용 가능 |
| 3 | SEC-007 IntegrityError 처리 | 小 | 즉시 적용 가능 |
| 4 | SEC-005 속도 제한 | 小 | slowapi 추가 |
| 5 | SEC-006 페이지네이션 | 中 | API 변경 동반 |
| 6 | SEC-009, SEC-010 설정 | 小 | 환경변수/미들웨어 |
