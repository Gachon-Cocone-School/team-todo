"""TC-T: Todo 관리 테스트"""

from fastapi.testclient import TestClient

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────


def create_user(
    client: TestClient, name: str = "홍길동", email: str = "hong@example.com"
):
    return client.post("/users", json={"name": name, "email": email}).json()


def create_todo(
    client: TestClient, title: str = "테스트 Todo", created_by: int = 1, **kwargs
):
    body = {"title": title, "created_by": created_by, **kwargs}
    return client.post("/todos", json=body)


# ── TC-T-01 Todo 목록 조회 ────────────────────────────────────────────────────


def test_list_todos_all(client: TestClient):
    user = create_user(client)
    create_todo(client, "Todo 1", user["id"])
    create_todo(client, "Todo 2", user["id"])
    res = client.get("/todos")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_list_todos_filter_status(client: TestClient):
    user = create_user(client)
    create_todo(client, "Todo 1", user["id"], status="in_progress")
    create_todo(client, "Todo 2", user["id"], status="done")
    res = client.get("/todos?status=in_progress")
    assert res.status_code == 200
    assert all(t["status"] == "in_progress" for t in res.json())
    assert len(res.json()) == 1


def test_list_todos_filter_priority(client: TestClient):
    user = create_user(client)
    create_todo(client, "High", user["id"], priority="high")
    create_todo(client, "Low", user["id"], priority="low")
    res = client.get("/todos?priority=high")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["priority"] == "high"


def test_list_todos_filter_assignee_id(client: TestClient):
    user1 = create_user(client, "user1", "u1@example.com")
    user2 = create_user(client, "user2", "u2@example.com")
    create_todo(client, "A", user1["id"], assignee_id=user1["id"])
    create_todo(client, "B", user1["id"], assignee_id=user2["id"])
    res = client.get(f"/todos?assignee_id={user1['id']}")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["assignee_id"] == user1["id"]


def test_list_todos_filter_tag_id(client: TestClient):
    user = create_user(client)
    tag = client.post("/tags", json={"name": "버그"}).json()
    todo_id = create_todo(client, "Tagged", user["id"]).json()["id"]
    client.post(f"/todos/{todo_id}/tags/{tag['id']}")
    res = client.get(f"/todos?tag_id={tag['id']}")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_list_todos_filter_combined(client: TestClient):
    user = create_user(client)
    create_todo(client, "A", user["id"], status="todo", priority="high")
    create_todo(client, "B", user["id"], status="todo", priority="low")
    create_todo(client, "C", user["id"], status="done", priority="high")
    res = client.get("/todos?status=todo&priority=high")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_list_todos_invalid_status(client: TestClient):
    res = client.get("/todos?status=invalid")
    assert res.status_code == 422


def test_list_todos_invalid_priority(client: TestClient):
    res = client.get("/todos?priority=urgent")
    assert res.status_code == 422


# ── TC-T-02 Todo 생성 ─────────────────────────────────────────────────────────


def test_create_todo_required_fields_only(client: TestClient):
    user = create_user(client)
    res = create_todo(client, "디자인 시안 검토", user["id"])
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "디자인 시안 검토"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"
    assert data["description"] is None
    assert data["due_date"] is None
    assert data["assignee_id"] is None
    assert data["created_by"] == user["id"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_todo_all_fields(client: TestClient):
    user1 = create_user(client, "user1", "u1@example.com")
    user2 = create_user(client, "user2", "u2@example.com")
    res = client.post(
        "/todos",
        json={
            "title": "API 구현",
            "description": "FastAPI 라우터 작성",
            "status": "in_progress",
            "priority": "high",
            "due_date": "2026-04-30",
            "assignee_id": user2["id"],
            "created_by": user1["id"],
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "API 구현"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"
    assert data["assignee_id"] == user2["id"]


def test_create_todo_missing_title(client: TestClient):
    user = create_user(client)
    res = client.post("/todos", json={"created_by": user["id"]})
    assert res.status_code == 422


def test_create_todo_missing_created_by(client: TestClient):
    res = client.post("/todos", json={"title": "API 구현"})
    assert res.status_code == 422


def test_create_todo_invalid_assignee(client: TestClient):
    user = create_user(client)
    res = client.post(
        "/todos",
        json={"title": "API 구현", "created_by": user["id"], "assignee_id": 999},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_create_todo_invalid_priority(client: TestClient):
    user = create_user(client)
    res = client.post(
        "/todos",
        json={"title": "API 구현", "created_by": user["id"], "priority": "urgent"},
    )
    assert res.status_code == 422


# ── TC-T-03 Todo 상세 조회 ────────────────────────────────────────────────────


def test_get_todo_with_tags(client: TestClient):
    user = create_user(client)
    tag = client.post("/tags", json={"name": "디자인", "color": "#FF5733"}).json()
    todo_id = create_todo(client, "디자인 시안 검토", user["id"]).json()["id"]
    client.post(f"/todos/{todo_id}/tags/{tag['id']}")
    res = client.get(f"/todos/{todo_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == todo_id
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "디자인"


def test_get_todo_not_found(client: TestClient):
    res = client.get("/todos/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Todo not found"


# ── TC-T-04 Todo 수정 ─────────────────────────────────────────────────────────


def test_update_todo_status(client: TestClient):
    user = create_user(client)
    todo_id = create_todo(client, created_by=user["id"]).json()["id"]
    res = client.put(f"/todos/{todo_id}", json={"status": "done"})
    assert res.status_code == 200
    assert res.json()["status"] == "done"


def test_update_todo_assignee(client: TestClient):
    user1 = create_user(client, "u1", "u1@example.com")
    user2 = create_user(client, "u2", "u2@example.com")
    todo_id = create_todo(client, created_by=user1["id"]).json()["id"]
    res = client.put(f"/todos/{todo_id}", json={"assignee_id": user2["id"]})
    assert res.status_code == 200
    assert res.json()["assignee_id"] == user2["id"]


def test_update_todo_clear_assignee(client: TestClient):
    user = create_user(client)
    todo_id = create_todo(client, created_by=user["id"], assignee_id=user["id"]).json()[
        "id"
    ]
    res = client.put(f"/todos/{todo_id}", json={"assignee_id": None})
    assert res.status_code == 200
    assert res.json()["assignee_id"] is None


def test_update_todo_not_found(client: TestClient):
    res = client.put("/todos/999", json={"status": "done"})
    assert res.status_code == 404
    assert res.json()["detail"] == "Todo not found"


def test_update_todo_invalid_status(client: TestClient):
    user = create_user(client)
    todo_id = create_todo(client, created_by=user["id"]).json()["id"]
    res = client.put(f"/todos/{todo_id}", json={"status": "cancelled"})
    assert res.status_code == 422


# ── TC-T-05 Todo 삭제 ─────────────────────────────────────────────────────────


def test_delete_todo_cascades(client: TestClient):
    user = create_user(client)
    todo_id = create_todo(client, created_by=user["id"]).json()["id"]
    comment_id = client.post(
        f"/todos/{todo_id}/comments",
        json={"author_id": user["id"], "content": "댓글"},
    ).json()["id"]

    res = client.delete(f"/todos/{todo_id}")
    assert res.status_code in (200, 204)
    assert client.get(f"/todos/{todo_id}").status_code == 404
    assert client.get(f"/comments/{comment_id}").status_code == 404


def test_delete_todo_not_found(client: TestClient):
    res = client.delete("/todos/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Todo not found"
