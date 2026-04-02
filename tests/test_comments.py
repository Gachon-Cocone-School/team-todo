"""TC-C: 댓글 관리 테스트"""

from fastapi.testclient import TestClient

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────


def create_user(
    client: TestClient, name: str = "홍길동", email: str = "hong@example.com"
):
    return client.post("/users", json={"name": name, "email": email}).json()


def create_todo(client: TestClient, user_id: int):
    return client.post(
        "/todos", json={"title": "테스트 Todo", "created_by": user_id}
    ).json()


def create_comment(
    client: TestClient, todo_id: int, author_id: int, content: str = "확인했습니다."
):
    return client.post(
        f"/todos/{todo_id}/comments",
        json={"author_id": author_id, "content": content},
    )


# ── TC-C-01 댓글 목록 조회 ────────────────────────────────────────────────────


def test_list_comments_success(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    create_comment(client, todo["id"], user["id"])
    res = client.get(f"/todos/{todo['id']}/comments")
    assert res.status_code == 200
    assert len(res.json()) == 1
    data = res.json()[0]
    assert data["todo_id"] == todo["id"]
    assert data["author_id"] == user["id"]
    assert data["content"] == "확인했습니다."


def test_list_comments_empty(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    res = client.get(f"/todos/{todo['id']}/comments")
    assert res.status_code == 200
    assert res.json() == []


def test_list_comments_todo_not_found(client: TestClient):
    res = client.get("/todos/999/comments")
    assert res.status_code == 404
    assert res.json()["detail"] == "Todo not found"


# ── TC-C-02 댓글 상세 조회 ────────────────────────────────────────────────────


def test_get_comment_success(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    comment_id = create_comment(client, todo["id"], user["id"]).json()["id"]
    res = client.get(f"/comments/{comment_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == comment_id
    assert "created_at" in data


def test_get_comment_not_found(client: TestClient):
    res = client.get("/comments/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Comment not found"


# ── TC-C-03 댓글 작성 ─────────────────────────────────────────────────────────


def test_create_comment_success(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    res = create_comment(client, todo["id"], user["id"])
    assert res.status_code == 201
    data = res.json()
    assert data["todo_id"] == todo["id"]
    assert data["author_id"] == user["id"]
    assert data["content"] == "확인했습니다."
    assert "id" in data
    assert "created_at" in data


def test_create_comment_missing_content(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    res = client.post(f"/todos/{todo['id']}/comments", json={"author_id": user["id"]})
    assert res.status_code == 422


def test_create_comment_missing_author_id(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    res = client.post(
        f"/todos/{todo['id']}/comments", json={"content": "확인했습니다."}
    )
    assert res.status_code == 422


def test_create_comment_todo_not_found(client: TestClient):
    user = create_user(client)
    res = client.post(
        "/todos/999/comments",
        json={"author_id": user["id"], "content": "확인했습니다."},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Todo not found"


def test_create_comment_author_not_found(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    res = client.post(
        f"/todos/{todo['id']}/comments",
        json={"author_id": 999, "content": "확인했습니다."},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


# ── TC-C-04 댓글 수정 ─────────────────────────────────────────────────────────


def test_update_comment_success(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    comment_id = create_comment(client, todo["id"], user["id"]).json()["id"]
    res = client.put(f"/comments/{comment_id}", json={"content": "수정된 내용입니다."})
    assert res.status_code == 200
    assert res.json()["content"] == "수정된 내용입니다."


def test_update_comment_not_found(client: TestClient):
    res = client.put("/comments/999", json={"content": "수정된 내용입니다."})
    assert res.status_code == 404
    assert res.json()["detail"] == "Comment not found"


def test_update_comment_empty_content(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    comment_id = create_comment(client, todo["id"], user["id"]).json()["id"]
    res = client.put(f"/comments/{comment_id}", json={"content": ""})
    assert res.status_code == 422


# ── TC-C-05 댓글 삭제 ─────────────────────────────────────────────────────────


def test_delete_comment_success(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    comment_id = create_comment(client, todo["id"], user["id"]).json()["id"]
    res = client.delete(f"/comments/{comment_id}")
    assert res.status_code in (200, 204)
    assert client.get(f"/comments/{comment_id}").status_code == 404


def test_delete_comment_not_found(client: TestClient):
    res = client.delete("/comments/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Comment not found"
