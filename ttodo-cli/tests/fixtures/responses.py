USER = {
    "id": 1,
    "name": "홍길동",
    "email": "hong@example.com",
    "created_at": "2024-01-01T00:00:00",
}

USER_2 = {
    "id": 2,
    "name": "김철수",
    "email": "kim@example.com",
    "created_at": "2024-01-01T00:00:00",
}

USER_LIST = [USER, USER_2]

TODO = {
    "id": 1,
    "title": "테스트 할일",
    "description": "설명",
    "status": "todo",
    "priority": "medium",
    "due_date": None,
    "assignee_id": None,
    "created_by": 1,
    "tags": [],
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

TODO_IN_PROGRESS = {**TODO, "id": 2, "status": "in_progress", "priority": "high"}

TODO_WITH_TAGS = {
    **TODO,
    "tags": [{"id": 1, "name": "버그", "color": "#ff0000"}],
}

TODO_LIST = [TODO, TODO_IN_PROGRESS]

TAG = {"id": 1, "name": "버그", "color": "#ff0000"}
TAG_2 = {"id": 2, "name": "기능", "color": "#00ff00"}
TAG_NO_COLOR = {"id": 3, "name": "리뷰", "color": None}
TAG_LIST = [TAG, TAG_2]

COMMENT = {
    "id": 1,
    "todo_id": 1,
    "author_id": 1,
    "content": "댓글 내용입니다",
    "created_at": "2024-01-01T00:00:00",
}

COMMENT_LIST = [COMMENT]

NOT_FOUND = {"detail": "찾을 수 없습니다"}
DELETED = {"message": "삭제 완료"}
ATTACHED = {"message": "태그 추가 완료"}
DETACHED = {"message": "태그 제거 완료"}
