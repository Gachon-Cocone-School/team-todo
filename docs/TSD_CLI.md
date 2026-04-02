# TSD: ttodo CLI 기술 명세

## 프로젝트 구조

```
ttodo-cli/
├── pyproject.toml           # 패키지 메타데이터 및 의존성
└── ttodo/
    ├── __init__.py
    ├── main.py              # Typer 앱 진입점, 서브커맨드 등록
    ├── state.py             # 전역 상태 (--json 플래그)
    ├── config.py            # 설정 파일 읽기/쓰기
    ├── client.py            # httpx HTTP 클라이언트 + 에러 처리
    ├── output.py            # Rich 테이블 / JSON 출력 헬퍼
    └── commands/
        ├── __init__.py
        ├── users.py         # user 서브커맨드
        ├── todos.py         # todo 서브커맨드
        ├── comments.py      # comment 서브커맨드
        ├── tags.py          # tag 서브커맨드
        └── settings.py      # config 서브커맨드
```

## 패키지 관리

```toml
# pyproject.toml
[project]
name = "ttodo"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "httpx>=0.27",
    "rich>=13",
]

[project.scripts]
ttodo = "ttodo.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 실행 방법

```bash
# 로컬 개발용
cd ttodo-cli
uv sync
uv run ttodo --help

# uvx로 실행 (로컬 패키지)
uvx --from ./ttodo-cli ttodo --help

# uvx로 실행 (PyPI 배포 후)
uvx ttodo --help
```

## 모듈 역할

### main.py

Typer 앱을 생성하고 5개의 서브커맨드를 등록한다.  
`--json` 전역 플래그를 콜백으로 받아 `state.json_output`에 기록한다.

```python
@app.callback()
def main(
    json: bool = typer.Option(
        False,
        "--json",
        help="Print the result as JSON instead of a formatted table. Useful for scripting.",
    )
) -> None:
    state.json_output = json
```

### state.py

`--json` 플래그를 전역으로 공유하기 위한 단일 상태 객체.  
모듈 임포트 시 싱글턴으로 동작하므로 별도 DI 없이 사용한다.

```python
class _State:
    json_output: bool = False

state = _State()
```

### config.py

| 함수 | 역할 |
|------|------|
| `load_config()` | TOML 파일 파싱 (stdlib `tomllib` 사용) |
| `save_config(config)` | TOML 파일 직접 쓰기 |
| `get_server_url()` | 설정값 반환, 없으면 기본값 |

설정 파일 경로: `~/.config/ttodo/config.toml`  
기본 서버 주소: `http://localhost:8000`

TOML 쓰기는 외부 라이브러리 없이 구현한다 (설정 구조가 단순하므로).

### client.py

`api_call(method, path, **kwargs)` 하나로 모든 HTTP 요청을 처리한다.

- `httpx.Client`를 컨텍스트 매니저로 사용 (커넥션 풀링)
- 서버 주소는 매 호출마다 `get_server_url()`에서 읽음
- `ConnectError` → 연결 실패 메시지 + `Exit(1)`
- `TimeoutException` → 타임아웃 메시지 + `Exit(1)`
- HTTP 4xx/5xx → 상태 코드 + detail 메시지 + `Exit(1)`

### output.py

| 함수 | 역할 |
|------|------|
| `print_json(data)` | `json.dumps`로 pretty print |
| `print_table(title, columns, rows)` | Rich `Table` (헤더 포함) |
| `print_record(title, data)` | Rich `Table` (키-값 2열) |

결과가 비어있으면 `print_table`이 "결과 없음"을 출력하고 종료한다.

### commands/*.py

각 파일은 `app = typer.Typer(...)` 를 최상위에 선언하고,  
`main.py`에서 `app.add_typer(sub_app, name="...")` 로 등록된다.

모든 커맨드 함수는 아래 패턴을 따른다:

```python
def some_command(...) -> None:
    data = api_call("METHOD", "/path", ...)
    if state.json_output:
        print_json(data)
    else:
        print_table(...) 또는 print_record(...)
```

## Help 텍스트 설계 원칙

모든 커맨드의 help 텍스트는 비개발자가 바로 이해할 수 있도록 plain English로 작성한다.

- **`app = typer.Typer(help=...)`**: 서브커맨드 그룹 전체 설명. 어떤 상황에서 이 그룹을 쓰는지, 예시 포함.
- **`@app.command(help=...)`**: 커맨드 단일 설명. 필수/선택 항목과 선택 가능한 값 나열.
- **`@app.command(epilog=...)`**: 실제 사용 예시 2–3개.
- **`typer.Option(help=...)`**: 옵션 하나의 용도. 예시값이나 단위 포함.
- **`typer.Argument(help=...)`**: 인자의 역할. "Run '...' to see all IDs" 패턴으로 탐색 방법 안내.

## 출력 문구 규칙

사용자에게 출력되는 메시지는 모두 영어로 작성한다.

| 상황 | 출력 예시 |
|------|-----------|
| 생성 완료 | `Team member created (ID: 1)` |
| 수정 완료 | `Todo updated (ID: 5)` |
| 삭제 완료 | `Comment #3 deleted.` |
| 태그 추가 | `Tag #2 attached to todo #1.` |
| 태그 제거 | `Tag #2 removed from todo #1.` |
| 서버 URL 저장 | `Server URL saved: http://...` |
| 설정 초기화 | `Settings reset. Server URL: http://localhost:8000` |
| 필드 누락 오류 | `Please specify at least one field to update.` |

## 레이어 구조

```
CLI 커맨드 (commands/*.py)
  └── api_call() (client.py)
        └── httpx.Client → Team Todo API 서버
```

- **commands**: 인자 파싱, 입력 유효성 검사, 출력 포맷 결정
- **client**: HTTP 요청 실행, 에러 처리 집중화
- **output**: 출력 형식 분리 (Rich / JSON)
- **config**: 설정 파일 I/O 분리

## Enum 정의 (commands/todos.py)

```python
class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
```

Typer가 Enum을 자동으로 인식해 유효성 검사 및 탭 완성을 지원한다.

## 파괴적 작업 보호

`delete` 커맨드는 `--yes` 플래그 없으면 `typer.confirm()`으로 확인을 받는다.

```python
if not yes:
    typer.confirm(f"Delete todo #{todo_id}? All its comments will also be deleted.", abort=True)
```

`abort=True`이면 사용자가 "n" 입력 시 `typer.Abort` 예외가 발생하고 종료된다.

각 커맨드별 확인 메시지:

| 커맨드 | 확인 메시지 |
|--------|-------------|
| `user delete` | `Delete team member #N? This cannot be undone.` |
| `todo delete` | `Delete todo #N? All its comments will also be deleted.` |
| `comment delete` | `Delete comment #N? This cannot be undone.` |
| `tag delete` | `Delete tag #N? This cannot be undone.` |
| `config reset` | `Reset settings to defaults?` |

## 에러 응답 형식

서버 오류 응답:
```json
{ "detail": "에러 메시지" }
```

CLI 출력 (stderr):
```
오류 404: Todo not found
오류 422: [{"loc": [...], "msg": "..."}]
서버 연결 실패: http://localhost:8000
서버 주소 확인: ttodo config show
시간 초과: http://localhost:8000
```

## 의존성 버전

| 패키지 | 버전 | 용도 |
|--------|------|------|
| typer | ≥0.12 | CLI 프레임워크 |
| httpx | ≥0.27 | HTTP 클라이언트 |
| rich | ≥13 | 터미널 출력 (테이블, 색상) |
| hatchling | - | 빌드 백엔드 (build-system) |

Python stdlib 사용:
- `tomllib` (3.11+): TOML 파싱
- `pathlib.Path`: 설정 파일 경로
- `json`: JSON 직렬화
- `enum.Enum`: Status / Priority 열거형
