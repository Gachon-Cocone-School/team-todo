"""TC-U: 팀원 관리 테스트"""

from fastapi.testclient import TestClient

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────


def create_user(
    client: TestClient, name: str = "홍길동", email: str = "hong@example.com"
):
    return client.post("/users", json={"name": name, "email": email})


# ── TC-U-01 팀원 목록 조회 ────────────────────────────────────────────────────


def test_list_users_empty(client: TestClient):
    res = client.get("/users")
    assert res.status_code == 200
    assert res.json() == []


def test_list_users_returns_all(client: TestClient):
    create_user(client, "홍길동", "hong@example.com")
    create_user(client, "김철수", "kim@example.com")
    res = client.get("/users")
    assert res.status_code == 200
    assert len(res.json()) == 2


# ── TC-U-02 팀원 상세 조회 ────────────────────────────────────────────────────


def test_get_user_success(client: TestClient):
    user_id = create_user(client).json()["id"]
    res = client.get(f"/users/{user_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == user_id
    assert data["name"] == "홍길동"
    assert data["email"] == "hong@example.com"
    assert "created_at" in data


def test_get_user_not_found(client: TestClient):
    res = client.get("/users/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


# ── TC-U-03 팀원 추가 ─────────────────────────────────────────────────────────


def test_create_user_success(client: TestClient):
    res = create_user(client)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "홍길동"
    assert data["email"] == "hong@example.com"
    assert "id" in data
    assert "created_at" in data


def test_create_user_missing_email(client: TestClient):
    res = client.post("/users", json={"name": "홍길동"})
    assert res.status_code == 422


def test_create_user_missing_name(client: TestClient):
    res = client.post("/users", json={"email": "hong@example.com"})
    assert res.status_code == 422


def test_create_user_duplicate_email(client: TestClient):
    create_user(client)
    res = create_user(client)
    assert res.status_code == 400
    assert res.json()["detail"] == "Email already exists"


# ── TC-U-04 팀원 수정 ─────────────────────────────────────────────────────────


def test_update_user_name(client: TestClient):
    user_id = create_user(client).json()["id"]
    res = client.put(f"/users/{user_id}", json={"name": "홍길동(수정)"})
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "홍길동(수정)"
    assert data["email"] == "hong@example.com"


def test_update_user_email(client: TestClient):
    user_id = create_user(client).json()["id"]
    res = client.put(f"/users/{user_id}", json={"email": "new@example.com"})
    assert res.status_code == 200
    assert res.json()["email"] == "new@example.com"


def test_update_user_not_found(client: TestClient):
    res = client.put("/users/999", json={"name": "홍길동"})
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_update_user_duplicate_email(client: TestClient):
    create_user(client, "홍길동", "hong@example.com")
    user2_id = create_user(client, "김철수", "kim@example.com").json()["id"]
    res = client.put(f"/users/{user2_id}", json={"email": "hong@example.com"})
    assert res.status_code == 400
    assert res.json()["detail"] == "Email already exists"


# ── TC-U-05 팀원 삭제 ─────────────────────────────────────────────────────────


def test_delete_user_success(client: TestClient):
    user_id = create_user(client).json()["id"]
    res = client.delete(f"/users/{user_id}")
    assert res.status_code in (200, 204)
    # 삭제 후 조회 시 404
    assert client.get(f"/users/{user_id}").status_code == 404


def test_delete_user_sets_assignee_null(client: TestClient):
    creator = create_user(client, "작성자", "creator@example.com").json()
    assignee = create_user(client, "담당자", "assignee@example.com").json()
    todo_res = client.post(
        "/todos",
        json={
            "title": "테스트 Todo",
            "created_by": creator["id"],
            "assignee_id": assignee["id"],
        },
    )
    todo_id = todo_res.json()["id"]

    client.delete(f"/users/{assignee['id']}")
    todo = client.get(f"/todos/{todo_id}").json()
    assert todo["assignee_id"] is None


def test_delete_user_cascades_comments(client: TestClient):
    author = create_user(client, "댓글작성자", "author@example.com").json()
    creator = create_user(client, "작성자", "creator@example.com").json()
    todo_id = client.post(
        "/todos", json={"title": "Todo", "created_by": creator["id"]}
    ).json()["id"]
    comment_id = client.post(
        f"/todos/{todo_id}/comments",
        json={"author_id": author["id"], "content": "확인했습니다."},
    ).json()["id"]

    client.delete(f"/users/{author['id']}")
    assert client.get(f"/comments/{comment_id}").status_code == 404


def test_delete_user_not_found(client: TestClient):
    res = client.delete("/users/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"
