"""TC-G: 태그 관리 테스트"""

from fastapi.testclient import TestClient

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────


def create_user(client: TestClient, email: str = "user@example.com"):
    return client.post("/users", json={"name": "테스터", "email": email}).json()


def create_todo(client: TestClient, user_id: int):
    return client.post(
        "/todos", json={"title": "테스트 Todo", "created_by": user_id}
    ).json()


def create_tag(client: TestClient, name: str = "디자인", color: str | None = "#FF5733"):
    body: dict = {"name": name}
    if color is not None:
        body["color"] = color
    return client.post("/tags", json=body)


# ── TC-G-01 태그 목록 조회 ────────────────────────────────────────────────────


def test_list_tags_all(client: TestClient):
    create_tag(client, "디자인")
    create_tag(client, "백엔드", "#3498DB")
    res = client.get("/tags")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_list_tags_empty(client: TestClient):
    res = client.get("/tags")
    assert res.status_code == 200
    assert res.json() == []


# ── TC-G-02 태그 상세 조회 ────────────────────────────────────────────────────


def test_get_tag_success(client: TestClient):
    tag_id = create_tag(client).json()["id"]
    res = client.get(f"/tags/{tag_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == tag_id
    assert data["name"] == "디자인"
    assert data["color"] == "#FF5733"


def test_get_tag_not_found(client: TestClient):
    res = client.get("/tags/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Tag not found"


# ── TC-G-03 태그 생성 ─────────────────────────────────────────────────────────


def test_create_tag_with_color(client: TestClient):
    res = create_tag(client, "디자인", "#FF5733")
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "디자인"
    assert data["color"] == "#FF5733"
    assert "id" in data


def test_create_tag_without_color(client: TestClient):
    res = client.post("/tags", json={"name": "백엔드"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "백엔드"
    assert data["color"] is None


def test_create_tag_missing_name(client: TestClient):
    res = client.post("/tags", json={"color": "#FF5733"})
    assert res.status_code == 422


def test_create_tag_duplicate_name(client: TestClient):
    create_tag(client, "디자인")
    res = create_tag(client, "디자인")
    assert res.status_code == 400
    assert res.json()["detail"] == "Tag name already exists"


# ── TC-G-04 태그 수정 ─────────────────────────────────────────────────────────


def test_update_tag_name(client: TestClient):
    tag_id = create_tag(client).json()["id"]
    res = client.put(f"/tags/{tag_id}", json={"name": "UI/UX"})
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "UI/UX"
    assert data["color"] == "#FF5733"


def test_update_tag_color(client: TestClient):
    tag_id = create_tag(client).json()["id"]
    res = client.put(f"/tags/{tag_id}", json={"color": "#2ECC71"})
    assert res.status_code == 200
    assert res.json()["color"] == "#2ECC71"


def test_update_tag_not_found(client: TestClient):
    res = client.put("/tags/999", json={"name": "UI/UX"})
    assert res.status_code == 404
    assert res.json()["detail"] == "Tag not found"


def test_update_tag_duplicate_name(client: TestClient):
    create_tag(client, "디자인")
    tag2_id = create_tag(client, "백엔드", "#3498DB").json()["id"]
    res = client.put(f"/tags/{tag2_id}", json={"name": "디자인"})
    assert res.status_code == 400
    assert res.json()["detail"] == "Tag name already exists"


# ── TC-G-05 태그 삭제 ─────────────────────────────────────────────────────────


def test_delete_tag_success(client: TestClient):
    tag_id = create_tag(client).json()["id"]
    res = client.delete(f"/tags/{tag_id}")
    assert res.status_code in (200, 204)
    assert client.get(f"/tags/{tag_id}").status_code == 404


def test_delete_tag_not_found(client: TestClient):
    res = client.delete("/tags/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Tag not found"


# ── TC-G-06 Todo에 태그 붙이기 ────────────────────────────────────────────────


def test_attach_tag_success(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    tag = create_tag(client).json()
    res = client.post(f"/todos/{todo['id']}/tags/{tag['id']}")
    assert res.status_code == 200
    todo_detail = client.get(f"/todos/{todo['id']}").json()
    assert any(t["id"] == tag["id"] for t in todo_detail["tags"])


def test_attach_tag_todo_not_found(client: TestClient):
    tag = create_tag(client).json()
    res = client.post(f"/todos/999/tags/{tag['id']}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Todo not found"


def test_attach_tag_tag_not_found(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    res = client.post(f"/todos/{todo['id']}/tags/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Tag not found"


def test_attach_tag_already_attached(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    tag = create_tag(client).json()
    client.post(f"/todos/{todo['id']}/tags/{tag['id']}")
    res = client.post(f"/todos/{todo['id']}/tags/{tag['id']}")
    assert res.status_code == 400
    assert res.json()["detail"] == "Tag already attached"


# ── TC-G-07 Todo에서 태그 떼기 ────────────────────────────────────────────────


def test_detach_tag_success(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    tag = create_tag(client).json()
    client.post(f"/todos/{todo['id']}/tags/{tag['id']}")
    res = client.delete(f"/todos/{todo['id']}/tags/{tag['id']}")
    assert res.status_code in (200, 204)
    todo_detail = client.get(f"/todos/{todo['id']}").json()
    assert not any(t["id"] == tag["id"] for t in todo_detail["tags"])


def test_detach_tag_todo_not_found(client: TestClient):
    tag = create_tag(client).json()
    res = client.delete(f"/todos/999/tags/{tag['id']}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Todo not found"


def test_detach_tag_not_attached(client: TestClient):
    user = create_user(client)
    todo = create_todo(client, user["id"])
    res = client.delete(f"/todos/{todo['id']}/tags/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Tag not attached"
