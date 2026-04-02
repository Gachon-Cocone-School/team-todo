# DATABASE: 팀 Todo 앱 DB 설계

## 테이블 목록

| 테이블 | 설명 |
|--------|------|
| `users` | 팀 멤버 |
| `todos` | Todo 항목 |
| `comments` | Todo 댓글 |
| `tags` | 태그 |
| `todo_tags` | Todo-Tag 다대다 중간 테이블 |

---

## 테이블 상세

### users

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 팀원 ID |
| `name` | VARCHAR(100) | NOT NULL | 이름 |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | 이메일 |
| `created_at` | DATETIME | NOT NULL, DEFAULT now | 생성일시 |

---

### todos

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | Todo ID |
| `title` | VARCHAR(255) | NOT NULL | 제목 |
| `description` | TEXT | NULLABLE | 상세 내용 |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'todo' | 상태 (todo / in_progress / done) |
| `priority` | VARCHAR(10) | NOT NULL, DEFAULT 'medium' | 우선순위 (low / medium / high) |
| `due_date` | DATE | NULLABLE | 마감일 |
| `assignee_id` | INTEGER | FK → users.id, NULLABLE | 담당자 |
| `created_by` | INTEGER | FK → users.id, NOT NULL | 생성자 |
| `created_at` | DATETIME | NOT NULL, DEFAULT now | 생성일시 |
| `updated_at` | DATETIME | NOT NULL, DEFAULT now | 수정일시 |

---

### comments

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 댓글 ID |
| `todo_id` | INTEGER | FK → todos.id, NOT NULL | 소속 Todo |
| `author_id` | INTEGER | FK → users.id, NOT NULL | 작성자 |
| `content` | TEXT | NOT NULL | 내용 |
| `created_at` | DATETIME | NOT NULL, DEFAULT now | 작성일시 |

---

### tags

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 태그 ID |
| `name` | VARCHAR(50) | NOT NULL, UNIQUE | 태그명 |
| `color` | VARCHAR(7) | NULLABLE | 색상 (예: #FF5733) |

---

### todo_tags (다대다 중간 테이블)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `todo_id` | INTEGER | FK → todos.id, NOT NULL | Todo |
| `tag_id` | INTEGER | FK → tags.id, NOT NULL | 태그 |

- PK: (`todo_id`, `tag_id`) 복합 기본키

---

## ERD

```
users
 ├─ todos.assignee_id  (1:N, nullable)
 ├─ todos.created_by   (1:N)
 └─ comments.author_id (1:N)

todos
 ├─ comments.todo_id   (1:N)
 └─ todo_tags.todo_id  (1:N)

tags
 └─ todo_tags.tag_id   (1:N)

todo_tags (todos ↔ tags 다대다 연결)
```

---

## 삭제 정책

| 관계 | 정책 |
|------|------|
| `users` 삭제 시 | `todos.assignee_id` → NULL 처리 (SET NULL), 작성한 `comments` CASCADE 삭제 |
| `todos` 삭제 시 | 연결된 `comments`, `todo_tags` CASCADE 삭제 |
| `tags` 삭제 시 | 연결된 `todo_tags` CASCADE 삭제 |
