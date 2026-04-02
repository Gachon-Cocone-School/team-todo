# TEST CASES: ttodo CLI

## 범례

- ✅ 성공 케이스
- ❌ 실패 케이스
- `[ ]` 미완료 / `[x]` 완료

---

## 사전 조건

```bash
# 서버 실행 중이어야 함
uv run uvicorn app.main:app --reload

# CLI 설치 확인
uvx --from ./ttodo-cli ttodo --help

# 서버 주소 설정
ttodo config set-server http://127.0.0.1:8000
```

---

## 0. config (설정)

### TC-CFG-01 서버 주소 설정

- [ ] ✅ **성공 - 서버 주소 설정**
  ```bash
  ttodo config set-server http://192.168.1.100:8000
  ```
  Expected: `Server URL saved: http://192.168.1.100:8000`  
  Expected: `~/.config/ttodo/config.toml` 파일에 URL 저장됨

- [ ] ✅ **성공 - 설정 확인**
  ```bash
  ttodo config show
  ```
  Expected: Server URL 과 Config File 경로가 테이블로 출력됨

- [ ] ✅ **성공 - 설정 확인 (JSON)**
  ```bash
  ttodo --json config show
  ```
  Expected:
  ```json
  {
    "server_url": "http://...",
    "config_file": "/Users/.../.config/ttodo/config.toml"
  }
  ```

- [ ] ✅ **성공 - 설정 초기화**
  ```bash
  ttodo config reset --yes
  ```
  Expected: `Settings reset. Server URL: http://localhost:8000`

---

## 1. user (팀 멤버 관리)

### TC-U-01 팀 멤버 목록 조회

- [ ] ✅ **성공 - 목록 테이블 출력**
  ```bash
  ttodo user list
  ```
  Expected: ID / Name / Email / Joined 컬럼의 Rich 테이블 출력

- [ ] ✅ **성공 - JSON 출력**
  ```bash
  ttodo --json user list
  ```
  Expected: JSON 배열 출력

- [ ] ✅ **성공 - 멤버 없을 때**
  ```bash
  ttodo user list  # DB 비어있을 때
  ```
  Expected: `결과 없음`

---

### TC-U-02 팀 멤버 생성

- [ ] ✅ **성공 - 멤버 생성**
  ```bash
  ttodo user create --name "Jane Smith" --email "jane@company.com"
  ```
  Expected: `Team member created (ID: N)` + 생성된 멤버 정보 출력

- [ ] ✅ **성공 - 단축 옵션 사용**
  ```bash
  ttodo user create -n "Jane Smith" -e "jane@company.com"
  ```
  Expected: `Team member created (ID: N)`

- [ ] ❌ **실패 - 이름 누락**
  ```bash
  ttodo user create --email "jane@company.com"
  ```
  Expected: Typer 오류 메시지 출력 (Missing option '--name')

- [ ] ❌ **실패 - 이메일 누락**
  ```bash
  ttodo user create --name "Jane Smith"
  ```
  Expected: Typer 오류 메시지 출력 (Missing option '--email')

---

### TC-U-03 팀 멤버 조회

- [ ] ✅ **성공 - 존재하는 멤버 조회**
  ```bash
  ttodo user get 1
  ```
  Expected: 멤버 정보 키-값 테이블 출력

- [ ] ❌ **실패 - 존재하지 않는 멤버**
  ```bash
  ttodo user get 999
  ```
  Expected: `오류 404: User not found` (stderr), exit code 1

---

### TC-U-04 팀 멤버 수정

- [ ] ✅ **성공 - 이름만 수정**
  ```bash
  ttodo user update 1 --name "Jane Lee"
  ```
  Expected: `Team member updated (ID: 1)`

- [ ] ✅ **성공 - 이메일만 수정**
  ```bash
  ttodo user update 1 --email "new@company.com"
  ```
  Expected: `Team member updated (ID: 1)`

- [ ] ❌ **실패 - 변경 항목 없음**
  ```bash
  ttodo user update 1
  ```
  Expected: `Please specify at least one field to update: --name or --email` (stderr), exit code 1

---

### TC-U-05 팀 멤버 삭제

- [ ] ✅ **성공 - 확인 후 삭제**
  ```bash
  ttodo user delete 1
  # 프롬프트: "Delete team member #1? This cannot be undone. [y/N]:" → y 입력
  ```
  Expected: `Team member #1 deleted.`

- [ ] ✅ **성공 - --yes 플래그로 확인 스킵**
  ```bash
  ttodo user delete 1 --yes
  ```
  Expected: `Team member #1 deleted.` (프롬프트 없음)

- [ ] ✅ **취소 - 확인 프롬프트에서 n 입력**
  ```bash
  ttodo user delete 1
  # 프롬프트: → n 입력
  ```
  Expected: `Aborted!` 출력, 삭제되지 않음

---

## 2. todo (할일 관리)

### TC-T-01 할일 목록 조회

- [ ] ✅ **성공 - 전체 목록**
  ```bash
  ttodo todo list
  ```
  Expected: ID / Title / Status / Priority / Due Date / Assignee / Tags 컬럼 테이블

- [ ] ✅ **성공 - 상태 필터**
  ```bash
  ttodo todo list --status in_progress
  ttodo todo list -s done
  ```
  Expected: 해당 상태의 할일만 출력

- [ ] ✅ **성공 - 우선순위 필터**
  ```bash
  ttodo todo list --priority high
  ttodo todo list -p low
  ```
  Expected: 해당 우선순위의 할일만 출력

- [ ] ✅ **성공 - 담당자 필터**
  ```bash
  ttodo todo list --assignee 1
  ttodo todo list -a 1
  ```
  Expected: assignee_id=1인 할일만 출력

- [ ] ✅ **성공 - 태그 필터**
  ```bash
  ttodo todo list --tag 2
  ttodo todo list -t 2
  ```
  Expected: tag_id=2가 달린 할일만 출력

- [ ] ✅ **성공 - 복합 필터**
  ```bash
  ttodo todo list --status todo --priority high --assignee 1
  ```
  Expected: 조건을 모두 만족하는 할일만 출력

- [ ] ❌ **실패 - 잘못된 status 값**
  ```bash
  ttodo todo list --status invalid
  ```
  Expected: Typer 오류 메시지 (Invalid value for '--status')

---

### TC-T-02 할일 생성

- [ ] ✅ **성공 - 필수 항목만**
  ```bash
  ttodo todo create --title "Fix login bug" --created-by 1
  ```
  Expected: `Todo created (ID: N)`

- [ ] ✅ **성공 - 모든 옵션 지정**
  ```bash
  ttodo todo create \
    --title "Write API docs" \
    --created-by 1 \
    --description "Cover all endpoints" \
    --status in_progress \
    --priority high \
    --due-date 2026-04-30 \
    --assignee 2
  ```
  Expected: `Todo created (ID: N)`

- [ ] ❌ **실패 - 제목 누락**
  ```bash
  ttodo todo create --created-by 1
  ```
  Expected: Typer 오류 메시지

- [ ] ❌ **실패 - 작성자 누락**
  ```bash
  ttodo todo create --title "Fix login bug"
  ```
  Expected: Typer 오류 메시지

---

### TC-T-03 할일 조회

- [ ] ✅ **성공 - 상세 조회 (태그 포함)**
  ```bash
  ttodo todo get 1
  ```
  Expected: 키-값 테이블 (태그 쉼표로 나열)

- [ ] ❌ **실패 - 존재하지 않는 할일**
  ```bash
  ttodo todo get 999
  ```
  Expected: `오류 404: Todo not found`, exit code 1

---

### TC-T-04 할일 수정

- [ ] ✅ **성공 - 상태만 변경**
  ```bash
  ttodo todo update 1 --status done
  ttodo todo update 1 -s done
  ```
  Expected: `Todo updated (ID: 1)`

- [ ] ✅ **성공 - 여러 항목 동시 변경**
  ```bash
  ttodo todo update 1 --priority low --assignee 2 --due-date 2026-05-01
  ```
  Expected: `Todo updated (ID: 1)`

- [ ] ❌ **실패 - 변경 항목 없음**
  ```bash
  ttodo todo update 1
  ```
  Expected: `Please specify at least one field to update.` (stderr), exit code 1

---

### TC-T-05 할일 삭제

- [ ] ✅ **성공 - --yes로 삭제**
  ```bash
  ttodo todo delete 1 --yes
  ```
  Expected: `Todo #1 deleted.`

- [ ] ✅ **취소 - 프롬프트에서 n**
  ```bash
  ttodo todo delete 1
  # → n 입력
  ```
  Expected: `Aborted!`, 삭제되지 않음

---

### TC-T-06 태그 연결

- [ ] ✅ **성공 - 태그 추가**
  ```bash
  ttodo todo attach-tag 1 2
  ```
  Expected: `Tag #2 attached to todo #1.`

- [ ] ✅ **성공 - 태그 제거**
  ```bash
  ttodo todo detach-tag 1 2
  ```
  Expected: `Tag #2 removed from todo #1.`

---

## 3. comment (댓글 관리)

### TC-C-01 댓글 목록 조회

- [ ] ✅ **성공 - 댓글 목록**
  ```bash
  ttodo comment list 1
  ```
  Expected: ID / Author / Content / Posted 컬럼 테이블

- [ ] ✅ **성공 - 댓글 없을 때**
  ```bash
  ttodo comment list 1  # 댓글 없는 할일
  ```
  Expected: `결과 없음`

---

### TC-C-02 댓글 작성

- [ ] ✅ **성공 - 댓글 작성**
  ```bash
  ttodo comment create 1 --author 1 --content "Started working on this"
  ttodo comment create 1 -a 1 -c "Blocked — need more info"
  ```
  Expected: `Comment posted (ID: N)`

- [ ] ❌ **실패 - 내용 누락**
  ```bash
  ttodo comment create 1 --author 1
  ```
  Expected: Typer 오류 메시지

---

### TC-C-03 댓글 조회

- [ ] ✅ **성공 - 댓글 상세 조회**
  ```bash
  ttodo comment get 1
  ```
  Expected: 키-값 테이블 (Todo, Author, Content, Posted 포함)

---

### TC-C-04 댓글 수정

- [ ] ✅ **성공 - 내용 수정**
  ```bash
  ttodo comment update 1 --content "Updated note"
  ttodo comment update 1 -c "Fixed typo"
  ```
  Expected: `Comment updated (ID: 1)`

---

### TC-C-05 댓글 삭제

- [ ] ✅ **성공 - --yes로 삭제**
  ```bash
  ttodo comment delete 1 --yes
  ```
  Expected: `Comment #1 deleted.`

- [ ] ✅ **취소 - 프롬프트에서 n**
  ```bash
  ttodo comment delete 1
  # 프롬프트: "Delete comment #1? This cannot be undone. [y/N]:" → n 입력
  ```
  Expected: `Aborted!`, 삭제되지 않음

---

## 4. tag (태그 관리)

### TC-TAG-01 태그 목록 조회

- [ ] ✅ **성공 - 태그 목록**
  ```bash
  ttodo tag list
  ```
  Expected: ID / Name / Color 컬럼 테이블

---

### TC-TAG-02 태그 생성

- [ ] ✅ **성공 - 이름만**
  ```bash
  ttodo tag create --name "urgent"
  ttodo tag create -n "feature"
  ```
  Expected: `Tag created (ID: N)`

- [ ] ✅ **성공 - 이름 + 색상**
  ```bash
  ttodo tag create --name "bug" --color "#ff0000"
  ```
  Expected: `Tag created (ID: N)`

- [ ] ❌ **실패 - 이름 누락**
  ```bash
  ttodo tag create --color "#ff0000"
  ```
  Expected: Typer 오류 메시지

---

### TC-TAG-03 태그 조회

- [ ] ✅ **성공 - 태그 상세 조회**
  ```bash
  ttodo tag get 1
  ```
  Expected: ID / Name / Color 키-값 테이블

---

### TC-TAG-04 태그 수정

- [ ] ✅ **성공 - 색상만 변경**
  ```bash
  ttodo tag update 1 --color "#00ff00"
  ```
  Expected: `Tag updated (ID: 1)`

- [ ] ❌ **실패 - 변경 항목 없음**
  ```bash
  ttodo tag update 1
  ```
  Expected: `Please specify at least one field to update: --name or --color` (stderr), exit code 1

---

### TC-TAG-05 태그 삭제

- [ ] ✅ **성공 - --yes로 삭제**
  ```bash
  ttodo tag delete 1 --yes
  ```
  Expected: `Tag #1 deleted.`

- [ ] ✅ **취소 - 프롬프트에서 n**
  ```bash
  ttodo tag delete 1
  # 프롬프트: "Delete tag #1? This cannot be undone. [y/N]:" → n 입력
  ```
  Expected: `Aborted!`, 삭제되지 않음

---

## 5. 전역 옵션

### TC-G-01 --json 플래그

- [ ] ✅ **성공 - 목록 JSON 출력**
  ```bash
  ttodo --json user list
  ttodo --json todo list
  ttodo --json tag list
  ```
  Expected: JSON 배열 출력

- [ ] ✅ **성공 - 단건 JSON 출력**
  ```bash
  ttodo --json user get 1
  ttodo --json todo get 1
  ```
  Expected: JSON 객체 출력

- [ ] ✅ **성공 - 필터 결합**
  ```bash
  ttodo --json todo list --status done --priority high
  ```
  Expected: 조건 만족하는 JSON 배열

---

## 6. 에러 처리

### TC-E-01 서버 연결 실패

- [ ] ❌ **실패 - 서버 미실행**
  ```bash
  ttodo config set-server http://127.0.0.1:9999
  ttodo user list
  ```
  Expected (stderr):
  ```
  서버 연결 실패: http://127.0.0.1:9999
  서버 주소 확인: ttodo config show
  ```
  Expected: exit code 1

### TC-E-02 잘못된 ID 타입

- [ ] ❌ **실패 - 문자열 ID 입력**
  ```bash
  ttodo user get abc
  ```
  Expected: Typer 오류 메시지 (Invalid value for 'USER_ID')
