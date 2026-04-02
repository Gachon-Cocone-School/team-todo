# PRD: 팀 Todo 앱 백엔드

## 개요

팀 멤버가 함께 사용하는 Todo 관리 백엔드 API.  
인증 없이 로컬 서버에서 운영하며, Swagger UI로 API 문서를 제공한다.

## 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.11+ |
| 프레임워크 | FastAPI |
| DB | SQLite |
| ORM | SQLAlchemy |
| 마이그레이션 | Alembic |
| API 문서 | Swagger UI (FastAPI 내장) |
| 인증 | 없음 |

## 기능 요구사항

### 팀원 관리 (Users)
- 팀원 목록 조회
- 팀원 상세 조회
- 팀원 추가
- 팀원 수정 (이름, 이메일)
- 팀원 삭제 (작성한 댓글 CASCADE 삭제, 담당 Todo의 assignee_id는 NULL 처리)

### Todo 관리
- Todo 목록 조회 (필터: 상태, 우선순위, 담당자, 태그)
- Todo 생성
- Todo 상세 조회
- Todo 수정 (제목, 설명, 담당자, 마감일, 우선순위, 상태)
- Todo 삭제

### 댓글 (Comments)
- 특정 Todo의 댓글 목록 조회
- 댓글 상세 조회
- 댓글 작성
- 댓글 수정 (내용)
- 댓글 삭제

### 태그 (Tags)
- 태그 목록 조회
- 태그 상세 조회
- 태그 생성
- 태그 수정 (이름, 색상)
- 태그 삭제
- Todo에 태그 붙이기 / 떼기

## 비기능 요구사항

- 로컬 서버 환경에서 운영 (팀 규모: 2~10명)
- Swagger UI (`/docs`)로 API 명세 제공
- 실시간 기능(WebSocket), 파일 첨부, 인증/인가는 범위 외

## API 엔드포인트

### Users
```
GET    /users            팀원 목록
POST   /users            팀원 추가
GET    /users/{id}       팀원 상세 조회
PUT    /users/{id}       팀원 수정
DELETE /users/{id}       팀원 삭제
```

### Todos
```
GET    /todos            목록 조회 (query: status, priority, assignee_id, tag_id)
POST   /todos            생성
GET    /todos/{id}       상세 조회
PUT    /todos/{id}       수정
DELETE /todos/{id}       삭제
```

### Comments
```
GET    /todos/{id}/comments     댓글 목록
POST   /todos/{id}/comments     댓글 작성
GET    /comments/{id}           댓글 상세 조회
PUT    /comments/{id}           댓글 수정
DELETE /comments/{id}           댓글 삭제
```

### Tags
```
GET    /tags                        태그 목록
POST   /tags                        태그 생성
GET    /tags/{id}                   태그 상세 조회
PUT    /tags/{id}                   태그 수정
DELETE /tags/{id}                   태그 삭제
POST   /todos/{id}/tags/{tag_id}    태그 붙이기
DELETE /todos/{id}/tags/{tag_id}    태그 떼기
```

