# Team Todo

[![CI](https://github.com/Gachon-Cocone-School/team-todo/actions/workflows/ci.yml/badge.svg)](https://github.com/Gachon-Cocone-School/team-todo/actions/workflows/ci.yml)

팀 멤버가 함께 사용하는 Todo 관리 API 서버 + CLI 도구.

- **백엔드**: FastAPI + SQLite (인증 없음, 로컬 운영)
- **CLI**: `ttodo` — 터미널에서 API를 바로 사용하는 도구

---

## 빠른 시작

### 1. 의존성 설치

```bash
uv sync
```

### 2. DB 초기화

```bash
uv run alembic upgrade head
```

### 3. 서버 실행

```bash
uv run uvicorn app.main:app --reload
```

API 문서: http://localhost:8000/docs

---

## CLI 도구 (ttodo)

### 설치 없이 바로 실행

```bash
uvx --from ./ttodo-cli ttodo --help
```

### 서버 주소 설정

```bash
ttodo config set-server http://localhost:8000
ttodo config show
```

기본값은 `http://localhost:8000`이므로 로컬에서 실행 중이라면 생략 가능.

---

## CLI 사용법

### 팀원 (user)

```bash
ttodo user list
ttodo user create --name "홍길동" --email hong@example.com
ttodo user get 1
ttodo user update 1 --name "홍길동(수정)"
ttodo user delete 1
```

### 할일 (todo)

```bash
# 목록 (필터 없음)
ttodo todo list

# 필터: 상태 / 우선순위 / 담당자 / 태그
ttodo todo list --status in_progress
ttodo todo list --priority high --assignee 2
ttodo todo list --tag 3

# 생성 (title, created-by 필수)
ttodo todo create --title "API 구현" --created-by 1
ttodo todo create --title "디자인 검토" --created-by 1 --assignee 2 --priority high --due-date 2026-04-30

# 수정 (변경할 항목만)
ttodo todo update 1 --status done
ttodo todo update 1 --assignee 2 --priority high

# 태그 관리
ttodo todo attach-tag 1 2
ttodo todo detach-tag 1 2

# 삭제
ttodo todo delete 1
```

### 댓글 (comment)

```bash
ttodo comment list 1
ttodo comment create 1 --author 2 --content "확인했습니다."
ttodo comment update 3 --content "수정된 내용"
ttodo comment delete 3
```

### 태그 (tag)

```bash
ttodo tag list
ttodo tag create --name "버그" --color "#FF5733"
ttodo tag update 1 --color "#2ECC71"
ttodo tag delete 1
```

### 전역 옵션

```bash
# JSON으로 출력 (스크립팅용)
ttodo --json todo list --status in_progress

# 도움말
ttodo --help
ttodo todo --help
ttodo todo create --help
```

---

## API 엔드포인트 요약

| 리소스 | 엔드포인트 | 설명 |
|--------|------------|------|
| 팀원 | `GET /users` | 목록 |
| | `POST /users` | 생성 |
| | `GET /users/{id}` | 상세 |
| | `PUT /users/{id}` | 수정 |
| | `DELETE /users/{id}` | 삭제 |
| 할일 | `GET /todos` | 목록 (필터: status, priority, assignee_id, tag_id) |
| | `POST /todos` | 생성 |
| | `GET /todos/{id}` | 상세 |
| | `PUT /todos/{id}` | 수정 |
| | `DELETE /todos/{id}` | 삭제 |
| 댓글 | `GET /todos/{id}/comments` | 목록 |
| | `POST /todos/{id}/comments` | 작성 |
| | `GET /comments/{id}` | 상세 |
| | `PUT /comments/{id}` | 수정 |
| | `DELETE /comments/{id}` | 삭제 |
| 태그 | `GET /tags` | 목록 |
| | `POST /tags` | 생성 |
| | `GET /tags/{id}` | 상세 |
| | `PUT /tags/{id}` | 수정 |
| | `DELETE /tags/{id}` | 삭제 |
| | `POST /todos/{id}/tags/{tag_id}` | 태그 붙이기 |
| | `DELETE /todos/{id}/tags/{tag_id}` | 태그 떼기 |

자세한 요청/응답 명세는 http://localhost:8000/docs 참고.

---

## 개발

### 코드 품질 검사

```bash
uv run ruff check --fix .   # 린트 자동 수정
uv run ruff format .        # 포맷
uv run mypy app/            # 타입 검사
uv run pytest tests/        # 테스트
uv run pylint app/          # 중복 코드 검사
```

커밋 시 위 검사가 pre-commit으로 자동 실행된다. 모두 통과해야 커밋된다.

### 패키지 관리

```bash
uv sync          # 의존성 설치
uv add <pkg>     # 패키지 추가
uv remove <pkg>  # 패키지 제거
```

---

## 문서

| 문서 | 설명 |
|------|------|
| [docs/PRD.md](docs/PRD.md) | 백엔드 기능 요구사항 |
| [docs/TSD.md](docs/TSD.md) | 백엔드 기술 명세 |
| [docs/DATABASE.md](docs/DATABASE.md) | DB 테이블 설계 및 ERD |
| [docs/PRD_CLI.md](docs/PRD_CLI.md) | CLI 기능 요구사항 및 커맨드 레퍼런스 |
| [docs/TSD_CLI.md](docs/TSD_CLI.md) | CLI 기술 명세 |
| [docs/TEST_CASES.md](docs/TEST_CASES.md) | 백엔드 테스트 케이스 |
| [docs/TEST_CASE_CLI.md](docs/TEST_CASE_CLI.md) | CLI 테스트 케이스 |
