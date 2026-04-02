# PRD: ttodo CLI

## 개요

`ttodo`는 Team Todo 백엔드 API를 터미널에서 사용할 수 있는 CLI 도구다.  
비개발자도 쉽게 사용할 수 있도록 설계하며, Mac/Linux/Windows를 모두 지원한다.

## 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.11+ |
| CLI 프레임워크 | Typer |
| HTTP 클라이언트 | httpx |
| 출력 | Rich (테이블/색상) |
| 패키지 관리 | uv |
| 배포 방식 | `uvx` (uv tool 실행) |

## 기능 요구사항

### 설정 관리 (config)
- 서버 주소 설정 (`~/.config/ttodo/config.toml`)
- 현재 설정 조회
- 설정 초기화 (기본값: `http://localhost:8000`)

### 유저 관리 (user)
- 유저 목록 조회
- 유저 상세 조회
- 유저 생성 (이름, 이메일)
- 유저 수정 (이름, 이메일 중 일부 가능)
- 유저 삭제 (삭제 전 확인 프롬프트, `--yes`로 스킵)

### 할일 관리 (todo)
- 할일 목록 조회 (필터: 상태, 우선순위, 담당자 ID, 태그 ID)
- 할일 상세 조회
- 할일 생성 (제목, 작성자 필수 / 나머지 선택)
- 할일 수정 (변경 항목만 선택 가능)
- 할일 삭제 (삭제 전 확인 프롬프트)
- 할일에 태그 추가
- 할일에서 태그 제거

### 댓글 관리 (comment)
- 특정 할일의 댓글 목록 조회
- 댓글 상세 조회
- 댓글 작성 (할일 ID, 작성자 ID, 내용)
- 댓글 수정 (내용)
- 댓글 삭제 (삭제 전 확인 프롬프트)

### 태그 관리 (tag)
- 태그 목록 조회
- 태그 상세 조회
- 태그 생성 (이름 필수, 색상 선택)
- 태그 수정 (이름, 색상 중 일부 가능)
- 태그 삭제 (삭제 전 확인 프롬프트)

## 비기능 요구사항

- **출력 형식**: 기본 Rich 테이블 / `--json` 플래그로 JSON 출력 전환
- **입력 방식**: 인자(Argument) + 옵션(Option)만 사용, 대화형 입력 없음
- **오류 처리**: 서버 연결 실패, 타임아웃, HTTP 4xx/5xx — 오류 메시지 출력 후 exit 1
- **파괴적 명령**: `delete`는 `--yes` 없으면 확인 프롬프트 표시
- **플랫폼**: Mac / Linux / Windows 지원
- **실행 방법**: `uvx --from ./ttodo-cli ttodo` 또는 PyPI 배포 후 `uvx ttodo`

## 커맨드 레퍼런스

### config

```bash
ttodo config show                          # Show current server URL and config file location
ttodo config set-server <URL>              # Save a new server URL
ttodo config reset [--yes]                 # Reset server URL back to the default
```

**설명:**  
Before using other commands, point ttodo at your server with `set-server`.  
Settings are saved to `~/.config/ttodo/config.toml` and persist across sessions.

### user

```bash
ttodo user list
ttodo user create --name <name> --email <email>
ttodo user get <ID>
ttodo user update <ID> [--name <name>] [--email <email>]
ttodo user delete <ID> [--yes]
```

**user create 옵션:**

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--name` / `-n` | ✅ | Full name of the team member  (e.g. Jane Smith) |
| `--email` / `-e` | ✅ | Email address. Must be unique across all team members. |

### todo

```bash
ttodo todo list [--status <status>] [--priority <priority>] [--assignee <ID>] [--tag <ID>]
ttodo todo create --title <title> --created-by <ID> [options...]
ttodo todo get <ID>
ttodo todo update <ID> [options...]
ttodo todo delete <ID> [--yes]
ttodo todo attach-tag <todo-ID> <tag-ID>
ttodo todo detach-tag <todo-ID> <tag-ID>
```

**todo create 옵션:**

| 옵션 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `--title` | ✅ | - | Short title describing what needs to be done |
| `--created-by` | ✅ | - | Your user ID — the person creating this todo |
| `--description` / `-d` | | - | Optional longer description with more details |
| `--status` / `-s` | | `todo` | Initial status: todo \| in_progress \| done |
| `--priority` / `-p` | | `medium` | How urgent is this: low \| medium \| high |
| `--due-date` | | - | Deadline in YYYY-MM-DD format  (e.g. 2026-04-30) |
| `--assignee` / `-a` | | - | User ID of the person responsible for completing this todo |

**todo list 필터 옵션:**

| 옵션 | 단축 | 설명 |
|------|------|------|
| `--status` | `-s` | Show only todos with this status: todo \| in_progress \| done |
| `--priority` | `-p` | Show only todos with this priority: low \| medium \| high |
| `--assignee` | `-a` | Show only todos assigned to this user ID |
| `--tag` | `-t` | Show only todos that have this tag ID attached |

### comment

```bash
ttodo comment list <todo-ID>
ttodo comment create <todo-ID> --author <ID> --content <text>
ttodo comment get <ID>
ttodo comment update <ID> --content <text>
ttodo comment delete <ID> [--yes]
```

**comment create 옵션:**

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--author` / `-a` | ✅ | Your user ID — the person writing this comment |
| `--content` / `-c` | ✅ | The text of your comment |

### tag

```bash
ttodo tag list
ttodo tag create --name <name> [--color <hex>]
ttodo tag get <ID>
ttodo tag update <ID> [--name <name>] [--color <hex>]
ttodo tag delete <ID> [--yes]
```

**tag create 옵션:**

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--name` / `-n` | ✅ | The label text for this tag  (e.g. 'bug', 'feature', 'urgent') |
| `--color` / `-c` | | A hex color code for this tag  (e.g. #ff0000 for red) |

## 전역 옵션

| 옵션 | 설명 |
|------|------|
| `--json` | Print the result as JSON instead of a formatted table. Useful for scripting. |
| `--help` | Show help message and exit. |

예시: `ttodo --json todo list --status in_progress`

## 출력 문구 (사용자에게 보이는 메시지)

| 상황 | 출력 (stdout) |
|------|---------------|
| 서버 URL 저장 | `Server URL saved: <url>` |
| 설정 초기화 | `Settings reset. Server URL: http://localhost:8000` |
| 팀 멤버 생성 | `Team member created (ID: N)` |
| 팀 멤버 수정 | `Team member updated (ID: N)` |
| 팀 멤버 삭제 | `Team member #N deleted.` |
| 할일 생성 | `Todo created (ID: N)` |
| 할일 수정 | `Todo updated (ID: N)` |
| 할일 삭제 | `Todo #N deleted.` |
| 태그 추가 | `Tag #N attached to todo #N.` |
| 태그 제거 | `Tag #N removed from todo #N.` |
| 댓글 작성 | `Comment posted (ID: N)` |
| 댓글 수정 | `Comment updated (ID: N)` |
| 댓글 삭제 | `Comment #N deleted.` |
| 태그 생성 | `Tag created (ID: N)` |
| 태그 수정 | `Tag updated (ID: N)` |
| 태그 삭제 | `Tag #N deleted.` |
| 결과 없음 | `결과 없음` (빈 테이블) |

## 설정 파일

위치: `~/.config/ttodo/config.toml`

```toml
[server]
url = "http://192.168.1.100:8000"
```

기본값: `http://localhost:8000`
