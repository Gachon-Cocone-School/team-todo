# TEST CASES: 팀 Todo 앱 백엔드

## 범례

- ✅ 성공 케이스
- ❌ 실패 케이스
- `[ ]` 미완료 / `[x]` 완료

---

## 1. Users (팀원 관리)

### TC-U-01 팀원 목록 조회

- [ ] ✅ **성공 - 팀원 목록 반환**
  - Endpoint: `GET /users`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    [
      { "id": 1, "name": "홍길동", "email": "hong@example.com", "created_at": "..." },
      { "id": 2, "name": "김철수", "email": "kim@example.com", "created_at": "..." }
    ]
    ```

- [ ] ✅ **성공 - 팀원이 없을 때 빈 배열 반환**
  - Endpoint: `GET /users`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    []
    ```

---

### TC-U-02 팀원 상세 조회

- [ ] ✅ **성공 - 존재하는 팀원 조회**
  - Endpoint: `GET /users/1`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    { "id": 1, "name": "홍길동", "email": "hong@example.com", "created_at": "..." }
    ```

- [ ] ❌ **실패 - 존재하지 않는 팀원 조회**
  - Endpoint: `GET /users/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "User not found" }
    ```

---

### TC-U-03 팀원 추가

- [ ] ✅ **성공 - 올바른 데이터로 팀원 생성**
  - Endpoint: `POST /users`
  - Request Body:
    ```json
    { "name": "홍길동", "email": "hong@example.com" }
    ```
  - Expected Response: `201 Created`
    ```json
    { "id": 1, "name": "홍길동", "email": "hong@example.com", "created_at": "..." }
    ```

- [ ] ❌ **실패 - 이메일 누락**
  - Endpoint: `POST /users`
  - Request Body:
    ```json
    { "name": "홍길동" }
    ```
  - Expected Response: `422 Unprocessable Entity`

- [ ] ❌ **실패 - 이름 누락**
  - Endpoint: `POST /users`
  - Request Body:
    ```json
    { "email": "hong@example.com" }
    ```
  - Expected Response: `422 Unprocessable Entity`

- [ ] ❌ **실패 - 중복 이메일**
  - Endpoint: `POST /users`
  - Request Body:
    ```json
    { "name": "홍길동2", "email": "hong@example.com" }
    ```
  - Expected Response: `400 Bad Request`
    ```json
    { "detail": "Email already exists" }
    ```

---

### TC-U-04 팀원 수정

- [ ] ✅ **성공 - 이름 수정**
  - Endpoint: `PUT /users/1`
  - Request Body:
    ```json
    { "name": "홍길동(수정)" }
    ```
  - Expected Response: `200 OK`
    ```json
    { "id": 1, "name": "홍길동(수정)", "email": "hong@example.com", "created_at": "..." }
    ```

- [ ] ✅ **성공 - 이메일 수정**
  - Endpoint: `PUT /users/1`
  - Request Body:
    ```json
    { "email": "new@example.com" }
    ```
  - Expected Response: `200 OK`
    ```json
    { "id": 1, "name": "홍길동", "email": "new@example.com", "created_at": "..." }
    ```

- [ ] ❌ **실패 - 존재하지 않는 팀원 수정**
  - Endpoint: `PUT /users/999`
  - Request Body:
    ```json
    { "name": "홍길동" }
    ```
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "User not found" }
    ```

- [ ] ❌ **실패 - 중복 이메일로 수정**
  - Endpoint: `PUT /users/1`
  - Request Body:
    ```json
    { "email": "kim@example.com" }
    ```
  - Expected Response: `400 Bad Request`
    ```json
    { "detail": "Email already exists" }
    ```

---

### TC-U-05 팀원 삭제

- [ ] ✅ **성공 - 존재하는 팀원 삭제**
  - Endpoint: `DELETE /users/1`
  - Request: 없음
  - Expected Response: `200 OK` (또는 `204 No Content`)

- [ ] ✅ **성공 - 담당자 삭제 시 Todo의 assignee_id가 NULL 처리**
  - Endpoint: `DELETE /users/1`
  - Request: 없음
  - Expected Response: `200 OK`, 해당 유저가 담당자였던 Todo의 `assignee_id`가 `null`로 변경됨

- [ ] ✅ **성공 - 팀원 삭제 시 작성한 댓글 CASCADE 삭제**
  - Endpoint: `DELETE /users/1`
  - Request: 없음
  - Expected Response: `200 OK`, 해당 유저가 작성한 댓글이 모두 삭제됨
  - 검증: `GET /comments/{id}` 로 삭제된 댓글 조회 시 `404 Not Found` 반환

- [ ] ❌ **실패 - 존재하지 않는 팀원 삭제**
  - Endpoint: `DELETE /users/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "User not found" }
    ```

---

## 2. Todos

### TC-T-01 Todo 목록 조회

- [ ] ✅ **성공 - 전체 목록 조회**
  - Endpoint: `GET /todos`
  - Request: 없음
  - Expected Response: `200 OK` — Todo 배열

- [ ] ✅ **성공 - status 필터**
  - Endpoint: `GET /todos?status=in_progress`
  - Request: 없음
  - Expected Response: `200 OK` — `status`가 `in_progress`인 Todo만 반환

- [ ] ✅ **성공 - priority 필터**
  - Endpoint: `GET /todos?priority=high`
  - Request: 없음
  - Expected Response: `200 OK` — `priority`가 `high`인 Todo만 반환

- [ ] ✅ **성공 - assignee_id 필터**
  - Endpoint: `GET /todos?assignee_id=1`
  - Request: 없음
  - Expected Response: `200 OK` — 담당자가 id=1인 Todo만 반환

- [ ] ✅ **성공 - tag_id 필터**
  - Endpoint: `GET /todos?tag_id=2`
  - Request: 없음
  - Expected Response: `200 OK` — 해당 태그가 붙은 Todo만 반환

- [ ] ✅ **성공 - 복합 필터**
  - Endpoint: `GET /todos?status=todo&priority=high`
  - Request: 없음
  - Expected Response: `200 OK` — 두 조건 모두 만족하는 Todo만 반환

- [ ] ❌ **실패 - 유효하지 않은 status 값**
  - Endpoint: `GET /todos?status=invalid`
  - Request: 없음
  - Expected Response: `422 Unprocessable Entity`

- [ ] ❌ **실패 - 유효하지 않은 priority 값**
  - Endpoint: `GET /todos?priority=urgent`
  - Request: 없음
  - Expected Response: `422 Unprocessable Entity`

---

### TC-T-02 Todo 생성

- [ ] ✅ **성공 - 필수 필드만으로 생성**
  - Endpoint: `POST /todos`
  - Request Body:
    ```json
    { "title": "디자인 시안 검토", "created_by": 1 }
    ```
  - Expected Response: `201 Created`
    ```json
    {
      "id": 1,
      "title": "디자인 시안 검토",
      "description": null,
      "status": "todo",
      "priority": "medium",
      "due_date": null,
      "assignee_id": null,
      "created_by": 1,
      "created_at": "...",
      "updated_at": "..."
    }
    ```

- [ ] ✅ **성공 - 모든 필드로 생성**
  - Endpoint: `POST /todos`
  - Request Body:
    ```json
    {
      "title": "API 구현",
      "description": "FastAPI 라우터 작성",
      "status": "in_progress",
      "priority": "high",
      "due_date": "2026-04-30",
      "assignee_id": 2,
      "created_by": 1
    }
    ```
  - Expected Response: `201 Created` — 입력값 그대로 반영된 Todo

- [ ] ❌ **실패 - title 누락**
  - Endpoint: `POST /todos`
  - Request Body:
    ```json
    { "created_by": 1 }
    ```
  - Expected Response: `422 Unprocessable Entity`

- [ ] ❌ **실패 - created_by 누락**
  - Endpoint: `POST /todos`
  - Request Body:
    ```json
    { "title": "API 구현" }
    ```
  - Expected Response: `422 Unprocessable Entity`

- [ ] ❌ **실패 - 존재하지 않는 assignee_id**
  - Endpoint: `POST /todos`
  - Request Body:
    ```json
    { "title": "API 구현", "created_by": 1, "assignee_id": 999 }
    ```
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "User not found" }
    ```

- [ ] ❌ **실패 - 유효하지 않은 priority 값**
  - Endpoint: `POST /todos`
  - Request Body:
    ```json
    { "title": "API 구현", "created_by": 1, "priority": "urgent" }
    ```
  - Expected Response: `422 Unprocessable Entity`

---

### TC-T-03 Todo 상세 조회

- [ ] ✅ **성공 - 존재하는 Todo 조회 (태그 포함)**
  - Endpoint: `GET /todos/1`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    {
      "id": 1,
      "title": "디자인 시안 검토",
      "tags": [{ "id": 1, "name": "디자인", "color": "#FF5733" }],
      ...
    }
    ```

- [ ] ❌ **실패 - 존재하지 않는 Todo 조회**
  - Endpoint: `GET /todos/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Todo not found" }
    ```

---

### TC-T-04 Todo 수정

- [ ] ✅ **성공 - 상태 변경**
  - Endpoint: `PUT /todos/1`
  - Request Body:
    ```json
    { "status": "done" }
    ```
  - Expected Response: `200 OK` — `status`가 `done`으로 변경된 Todo

- [ ] ✅ **성공 - 담당자 변경**
  - Endpoint: `PUT /todos/1`
  - Request Body:
    ```json
    { "assignee_id": 2 }
    ```
  - Expected Response: `200 OK` — `assignee_id`가 2로 변경된 Todo

- [ ] ✅ **성공 - 담당자 해제 (null)**
  - Endpoint: `PUT /todos/1`
  - Request Body:
    ```json
    { "assignee_id": null }
    ```
  - Expected Response: `200 OK` — `assignee_id`가 `null`인 Todo

- [ ] ❌ **실패 - 존재하지 않는 Todo 수정**
  - Endpoint: `PUT /todos/999`
  - Request Body:
    ```json
    { "status": "done" }
    ```
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Todo not found" }
    ```

- [ ] ❌ **실패 - 유효하지 않은 status 값**
  - Endpoint: `PUT /todos/1`
  - Request Body:
    ```json
    { "status": "cancelled" }
    ```
  - Expected Response: `422 Unprocessable Entity`

---

### TC-T-05 Todo 삭제

- [ ] ✅ **성공 - 존재하는 Todo 삭제 (댓글, 태그 연결도 함께 삭제)**
  - Endpoint: `DELETE /todos/1`
  - Request: 없음
  - Expected Response: `200 OK` (또는 `204 No Content`)

- [ ] ❌ **실패 - 존재하지 않는 Todo 삭제**
  - Endpoint: `DELETE /todos/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Todo not found" }
    ```

---

## 3. Comments (댓글)

### TC-C-01 댓글 목록 조회

- [ ] ✅ **성공 - 특정 Todo의 댓글 목록 반환**
  - Endpoint: `GET /todos/1/comments`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    [
      { "id": 1, "todo_id": 1, "author_id": 2, "content": "확인했습니다.", "created_at": "..." }
    ]
    ```

- [ ] ✅ **성공 - 댓글이 없을 때 빈 배열 반환**
  - Endpoint: `GET /todos/1/comments`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    []
    ```

- [ ] ❌ **실패 - 존재하지 않는 Todo의 댓글 목록 조회**
  - Endpoint: `GET /todos/999/comments`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Todo not found" }
    ```

---

### TC-C-02 댓글 상세 조회

- [ ] ✅ **성공 - 존재하는 댓글 조회**
  - Endpoint: `GET /comments/1`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    { "id": 1, "todo_id": 1, "author_id": 2, "content": "확인했습니다.", "created_at": "..." }
    ```

- [ ] ❌ **실패 - 존재하지 않는 댓글 조회**
  - Endpoint: `GET /comments/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Comment not found" }
    ```

---

### TC-C-03 댓글 작성

- [ ] ✅ **성공 - 정상 댓글 작성**
  - Endpoint: `POST /todos/1/comments`
  - Request Body:
    ```json
    { "author_id": 2, "content": "확인했습니다." }
    ```
  - Expected Response: `201 Created`
    ```json
    { "id": 1, "todo_id": 1, "author_id": 2, "content": "확인했습니다.", "created_at": "..." }
    ```

- [ ] ❌ **실패 - content 누락**
  - Endpoint: `POST /todos/1/comments`
  - Request Body:
    ```json
    { "author_id": 2 }
    ```
  - Expected Response: `422 Unprocessable Entity`

- [ ] ❌ **실패 - author_id 누락**
  - Endpoint: `POST /todos/1/comments`
  - Request Body:
    ```json
    { "content": "확인했습니다." }
    ```
  - Expected Response: `422 Unprocessable Entity`

- [ ] ❌ **실패 - 존재하지 않는 Todo에 댓글 작성**
  - Endpoint: `POST /todos/999/comments`
  - Request Body:
    ```json
    { "author_id": 2, "content": "확인했습니다." }
    ```
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Todo not found" }
    ```

- [ ] ❌ **실패 - 존재하지 않는 author_id**
  - Endpoint: `POST /todos/1/comments`
  - Request Body:
    ```json
    { "author_id": 999, "content": "확인했습니다." }
    ```
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "User not found" }
    ```

---

### TC-C-04 댓글 수정

- [ ] ✅ **성공 - 내용 수정**
  - Endpoint: `PUT /comments/1`
  - Request Body:
    ```json
    { "content": "수정된 내용입니다." }
    ```
  - Expected Response: `200 OK`
    ```json
    { "id": 1, "todo_id": 1, "author_id": 2, "content": "수정된 내용입니다.", "created_at": "..." }
    ```

- [ ] ❌ **실패 - 존재하지 않는 댓글 수정**
  - Endpoint: `PUT /comments/999`
  - Request Body:
    ```json
    { "content": "수정된 내용입니다." }
    ```
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Comment not found" }
    ```

- [ ] ❌ **실패 - content 빈 문자열**
  - Endpoint: `PUT /comments/1`
  - Request Body:
    ```json
    { "content": "" }
    ```
  - Expected Response: `422 Unprocessable Entity`

---

### TC-C-05 댓글 삭제

- [ ] ✅ **성공 - 존재하는 댓글 삭제**
  - Endpoint: `DELETE /comments/1`
  - Request: 없음
  - Expected Response: `200 OK` (또는 `204 No Content`)

- [ ] ❌ **실패 - 존재하지 않는 댓글 삭제**
  - Endpoint: `DELETE /comments/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Comment not found" }
    ```

---

## 4. Tags (태그)

### TC-G-01 태그 목록 조회

- [ ] ✅ **성공 - 전체 태그 목록 반환**
  - Endpoint: `GET /tags`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    [
      { "id": 1, "name": "디자인", "color": "#FF5733" },
      { "id": 2, "name": "백엔드", "color": "#3498DB" }
    ]
    ```

- [ ] ✅ **성공 - 태그가 없을 때 빈 배열 반환**
  - Endpoint: `GET /tags`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    []
    ```

---

### TC-G-02 태그 상세 조회

- [ ] ✅ **성공 - 존재하는 태그 조회**
  - Endpoint: `GET /tags/1`
  - Request: 없음
  - Expected Response: `200 OK`
    ```json
    { "id": 1, "name": "디자인", "color": "#FF5733" }
    ```

- [ ] ❌ **실패 - 존재하지 않는 태그 조회**
  - Endpoint: `GET /tags/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Tag not found" }
    ```

---

### TC-G-03 태그 생성

- [ ] ✅ **성공 - 이름과 색상으로 태그 생성**
  - Endpoint: `POST /tags`
  - Request Body:
    ```json
    { "name": "디자인", "color": "#FF5733" }
    ```
  - Expected Response: `201 Created`
    ```json
    { "id": 1, "name": "디자인", "color": "#FF5733" }
    ```

- [ ] ✅ **성공 - 색상 없이 태그 생성**
  - Endpoint: `POST /tags`
  - Request Body:
    ```json
    { "name": "백엔드" }
    ```
  - Expected Response: `201 Created`
    ```json
    { "id": 2, "name": "백엔드", "color": null }
    ```

- [ ] ❌ **실패 - name 누락**
  - Endpoint: `POST /tags`
  - Request Body:
    ```json
    { "color": "#FF5733" }
    ```
  - Expected Response: `422 Unprocessable Entity`

- [ ] ❌ **실패 - 중복 태그명**
  - Endpoint: `POST /tags`
  - Request Body:
    ```json
    { "name": "디자인" }
    ```
  - Expected Response: `400 Bad Request`
    ```json
    { "detail": "Tag name already exists" }
    ```

---

### TC-G-04 태그 수정

- [ ] ✅ **성공 - 이름 수정**
  - Endpoint: `PUT /tags/1`
  - Request Body:
    ```json
    { "name": "UI/UX" }
    ```
  - Expected Response: `200 OK`
    ```json
    { "id": 1, "name": "UI/UX", "color": "#FF5733" }
    ```

- [ ] ✅ **성공 - 색상 수정**
  - Endpoint: `PUT /tags/1`
  - Request Body:
    ```json
    { "color": "#2ECC71" }
    ```
  - Expected Response: `200 OK`
    ```json
    { "id": 1, "name": "디자인", "color": "#2ECC71" }
    ```

- [ ] ❌ **실패 - 존재하지 않는 태그 수정**
  - Endpoint: `PUT /tags/999`
  - Request Body:
    ```json
    { "name": "UI/UX" }
    ```
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Tag not found" }
    ```

- [ ] ❌ **실패 - 중복 태그명으로 수정**
  - Endpoint: `PUT /tags/1`
  - Request Body:
    ```json
    { "name": "백엔드" }
    ```
  - Expected Response: `400 Bad Request`
    ```json
    { "detail": "Tag name already exists" }
    ```

---

### TC-G-05 태그 삭제

- [ ] ✅ **성공 - 존재하는 태그 삭제 (Todo 연결도 함께 해제)**
  - Endpoint: `DELETE /tags/1`
  - Request: 없음
  - Expected Response: `200 OK` (또는 `204 No Content`)

- [ ] ❌ **실패 - 존재하지 않는 태그 삭제**
  - Endpoint: `DELETE /tags/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Tag not found" }
    ```

---

### TC-G-06 Todo에 태그 붙이기

- [ ] ✅ **성공 - Todo에 태그 추가**
  - Endpoint: `POST /todos/1/tags/1`
  - Request: 없음
  - Expected Response: `200 OK`

- [ ] ❌ **실패 - 존재하지 않는 Todo**
  - Endpoint: `POST /todos/999/tags/1`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Todo not found" }
    ```

- [ ] ❌ **실패 - 존재하지 않는 태그**
  - Endpoint: `POST /todos/1/tags/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Tag not found" }
    ```

- [ ] ❌ **실패 - 이미 붙어있는 태그 중복 추가**
  - Endpoint: `POST /todos/1/tags/1`
  - Request: 없음
  - Expected Response: `400 Bad Request`
    ```json
    { "detail": "Tag already attached" }
    ```

---

### TC-G-07 Todo에서 태그 떼기

- [ ] ✅ **성공 - Todo에서 태그 제거**
  - Endpoint: `DELETE /todos/1/tags/1`
  - Request: 없음
  - Expected Response: `200 OK` (또는 `204 No Content`)

- [ ] ❌ **실패 - 존재하지 않는 Todo**
  - Endpoint: `DELETE /todos/999/tags/1`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Todo not found" }
    ```

- [ ] ❌ **실패 - 붙어있지 않은 태그 제거 시도**
  - Endpoint: `DELETE /todos/1/tags/999`
  - Request: 없음
  - Expected Response: `404 Not Found`
    ```json
    { "detail": "Tag not attached" }
    ```
