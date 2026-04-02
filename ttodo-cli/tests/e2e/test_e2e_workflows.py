"""E2E 워크플로우 테스트 — 실제 서버와의 전체 스택 통합 검증."""

from ttodo.main import app

from tests.e2e.conftest import invoke_json

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def run(runner, *args):
    """CliRunner로 CLI를 실행하고 result를 반환한다."""
    return runner.invoke(app, list(args))


def run_json(runner, *args):
    """--json 플래그로 CLI를 실행하고 파싱된 dict/list를 반환한다."""
    return invoke_json(runner, list(args))


# ---------------------------------------------------------------------------
# 1. 유저(팀 멤버) 전체 수명 주기
# ---------------------------------------------------------------------------


class TestE2EUserWorkflow:
    """create → list → get → update(name) → update(email) → delete"""

    def test_create_user(self, cli):
        data = run_json(
            cli,
            "user",
            "create",
            "--name",
            "E2E 홍길동",
            "--email",
            "e2e_hong@test.com",
        )
        assert data["name"] == "E2E 홍길동"
        assert data["email"] == "e2e_hong@test.com"
        assert "id" in data
        TestE2EUserWorkflow.user_id = data["id"]

    def test_user_appears_in_list(self, cli):
        data = run_json(cli, "user", "list")
        ids = [u["id"] for u in data]
        assert TestE2EUserWorkflow.user_id in ids

    def test_get_user(self, cli):
        data = run_json(cli, "user", "get", str(TestE2EUserWorkflow.user_id))
        assert data["id"] == TestE2EUserWorkflow.user_id
        assert data["email"] == "e2e_hong@test.com"

    def test_update_user_name(self, cli):
        result = run(
            cli,
            "user",
            "update",
            str(TestE2EUserWorkflow.user_id),
            "--name",
            "E2E 이름변경",
        )
        assert result.exit_code == 0
        assert "Team member updated" in result.output
        # 변경 확인
        data = run_json(cli, "user", "get", str(TestE2EUserWorkflow.user_id))
        assert data["name"] == "E2E 이름변경"

    def test_update_user_email(self, cli):
        result = run(
            cli,
            "user",
            "update",
            str(TestE2EUserWorkflow.user_id),
            "--email",
            "e2e_updated@test.com",
        )
        assert result.exit_code == 0
        data = run_json(cli, "user", "get", str(TestE2EUserWorkflow.user_id))
        assert data["email"] == "e2e_updated@test.com"

    def test_delete_user(self, cli):
        result = run(cli, "user", "delete", str(TestE2EUserWorkflow.user_id), "--yes")
        assert result.exit_code == 0
        assert "deleted." in result.output

    def test_user_gone_after_delete(self, cli):
        result = run(cli, "user", "get", str(TestE2EUserWorkflow.user_id))
        assert result.exit_code == 1
        assert "404" in result.stderr


# ---------------------------------------------------------------------------
# 2. 할일(Todo) 전체 수명 주기
# ---------------------------------------------------------------------------


class TestE2ETodoWorkflow:
    """유저 생성 → todo CRUD → 필터 → 삭제"""

    def test_setup_user(self, cli):
        data = run_json(
            cli,
            "user",
            "create",
            "--name",
            "Todo작성자",
            "--email",
            "todo_author@test.com",
        )
        TestE2ETodoWorkflow.author_id = data["id"]

    def test_create_todo_minimal(self, cli):
        data = run_json(
            cli,
            "todo",
            "create",
            "--title",
            "E2E 기본 할일",
            "--created-by",
            str(TestE2ETodoWorkflow.author_id),
        )
        assert data["title"] == "E2E 기본 할일"
        assert data["status"] == "todo"
        assert data["priority"] == "medium"
        TestE2ETodoWorkflow.todo_id = data["id"]

    def test_create_todo_full_options(self, cli):
        data = run_json(
            cli,
            "todo",
            "create",
            "--title",
            "E2E 전체옵션 할일",
            "--created-by",
            str(TestE2ETodoWorkflow.author_id),
            "--description",
            "E2E 상세설명",
            "--status",
            "in_progress",
            "--priority",
            "high",
            "--due-date",
            "2026-12-31",
            "--assignee",
            str(TestE2ETodoWorkflow.author_id),
        )
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"
        assert data["due_date"] == "2026-12-31"
        TestE2ETodoWorkflow.todo_id2 = data["id"]

    def test_list_todos_no_filter(self, cli):
        data = run_json(cli, "todo", "list")
        ids = [t["id"] for t in data]
        assert TestE2ETodoWorkflow.todo_id in ids
        assert TestE2ETodoWorkflow.todo_id2 in ids

    def test_list_todos_status_filter(self, cli):
        data = run_json(cli, "todo", "list", "--status", "in_progress")
        statuses = [t["status"] for t in data]
        assert all(s == "in_progress" for s in statuses)
        ids = [t["id"] for t in data]
        assert TestE2ETodoWorkflow.todo_id2 in ids

    def test_list_todos_priority_filter(self, cli):
        data = run_json(cli, "todo", "list", "--priority", "high")
        priorities = [t["priority"] for t in data]
        assert all(p == "high" for p in priorities)

    def test_get_todo(self, cli):
        data = run_json(cli, "todo", "get", str(TestE2ETodoWorkflow.todo_id))
        assert data["id"] == TestE2ETodoWorkflow.todo_id
        assert data["title"] == "E2E 기본 할일"
        assert data["tags"] == []

    def test_update_todo_status(self, cli):
        result = run(
            cli, "todo", "update", str(TestE2ETodoWorkflow.todo_id), "--status", "done"
        )
        assert result.exit_code == 0
        assert "Todo updated" in result.output
        data = run_json(cli, "todo", "get", str(TestE2ETodoWorkflow.todo_id))
        assert data["status"] == "done"

    def test_delete_todo(self, cli):
        result = run(cli, "todo", "delete", str(TestE2ETodoWorkflow.todo_id), "--yes")
        assert result.exit_code == 0
        assert "deleted." in result.output

    def test_todo_gone_after_delete(self, cli):
        result = run(cli, "todo", "get", str(TestE2ETodoWorkflow.todo_id))
        assert result.exit_code == 1
        assert "404" in result.stderr

    def test_teardown(self, cli):
        run(cli, "todo", "delete", str(TestE2ETodoWorkflow.todo_id2), "--yes")
        run(cli, "user", "delete", str(TestE2ETodoWorkflow.author_id), "--yes")


# ---------------------------------------------------------------------------
# 3. 댓글(Comment) 전체 수명 주기
# ---------------------------------------------------------------------------


class TestE2ECommentWorkflow:
    """유저+할일 생성 → comment CRUD → 정리"""

    def test_setup(self, cli):
        user = run_json(
            cli,
            "user",
            "create",
            "--name",
            "댓글작성자",
            "--email",
            "commenter@test.com",
        )
        TestE2ECommentWorkflow.user_id = user["id"]
        todo = run_json(
            cli,
            "todo",
            "create",
            "--title",
            "댓글 테스트용 할일",
            "--created-by",
            str(user["id"]),
        )
        TestE2ECommentWorkflow.todo_id = todo["id"]

    def test_create_comment(self, cli):
        data = run_json(
            cli,
            "comment",
            "create",
            str(TestE2ECommentWorkflow.todo_id),
            "--author",
            str(TestE2ECommentWorkflow.user_id),
            "--content",
            "E2E 첫 번째 댓글",
        )
        assert data["content"] == "E2E 첫 번째 댓글"
        assert data["todo_id"] == TestE2ECommentWorkflow.todo_id
        TestE2ECommentWorkflow.comment_id = data["id"]

    def test_list_comments(self, cli):
        data = run_json(cli, "comment", "list", str(TestE2ECommentWorkflow.todo_id))
        ids = [c["id"] for c in data]
        assert TestE2ECommentWorkflow.comment_id in ids

    def test_get_comment(self, cli):
        data = run_json(cli, "comment", "get", str(TestE2ECommentWorkflow.comment_id))
        assert data["id"] == TestE2ECommentWorkflow.comment_id
        assert data["content"] == "E2E 첫 번째 댓글"
        assert data["todo_id"] == TestE2ECommentWorkflow.todo_id

    def test_update_comment(self, cli):
        result = run(
            cli,
            "comment",
            "update",
            str(TestE2ECommentWorkflow.comment_id),
            "--content",
            "E2E 수정된 댓글",
        )
        assert result.exit_code == 0
        assert "Comment updated" in result.output
        data = run_json(cli, "comment", "get", str(TestE2ECommentWorkflow.comment_id))
        assert data["content"] == "E2E 수정된 댓글"

    def test_delete_comment(self, cli):
        result = run(
            cli, "comment", "delete", str(TestE2ECommentWorkflow.comment_id), "--yes"
        )
        assert result.exit_code == 0
        assert "deleted." in result.output

    def test_comment_gone_after_delete(self, cli):
        result = run(cli, "comment", "get", str(TestE2ECommentWorkflow.comment_id))
        assert result.exit_code == 1
        assert "404" in result.stderr

    def test_teardown(self, cli):
        run(cli, "todo", "delete", str(TestE2ECommentWorkflow.todo_id), "--yes")
        run(cli, "user", "delete", str(TestE2ECommentWorkflow.user_id), "--yes")


# ---------------------------------------------------------------------------
# 4. 태그(Tag) 전체 수명 주기 + 할일 연결
# ---------------------------------------------------------------------------


class TestE2ETagWorkflow:
    """tag CRUD → todo에 attach/detach → 태그 포함 여부 확인"""

    def test_create_tag_name_only(self, cli):
        data = run_json(cli, "tag", "create", "--name", "E2E-태그-이름만")
        assert data["name"] == "E2E-태그-이름만"
        TestE2ETagWorkflow.tag_id1 = data["id"]

    def test_create_tag_with_color(self, cli):
        data = run_json(
            cli, "tag", "create", "--name", "E2E-태그-색상포함", "--color", "#e2e2e2"
        )
        assert data["color"] == "#e2e2e2"
        TestE2ETagWorkflow.tag_id2 = data["id"]

    def test_list_tags(self, cli):
        data = run_json(cli, "tag", "list")
        ids = [t["id"] for t in data]
        assert TestE2ETagWorkflow.tag_id1 in ids
        assert TestE2ETagWorkflow.tag_id2 in ids

    def test_get_tag(self, cli):
        data = run_json(cli, "tag", "get", str(TestE2ETagWorkflow.tag_id2))
        assert data["color"] == "#e2e2e2"

    def test_update_tag(self, cli):
        result = run(
            cli,
            "tag",
            "update",
            str(TestE2ETagWorkflow.tag_id1),
            "--name",
            "E2E-태그-이름변경",
        )
        assert result.exit_code == 0
        assert "Tag updated" in result.output
        data = run_json(cli, "tag", "get", str(TestE2ETagWorkflow.tag_id1))
        assert data["name"] == "E2E-태그-이름변경"

    def test_setup_user_and_todo(self, cli):
        user = run_json(
            cli,
            "user",
            "create",
            "--name",
            "태그테스터",
            "--email",
            "tag_tester@test.com",
        )
        TestE2ETagWorkflow.user_id = user["id"]
        todo = run_json(
            cli,
            "todo",
            "create",
            "--title",
            "태그 연결 테스트 할일",
            "--created-by",
            str(user["id"]),
        )
        TestE2ETagWorkflow.todo_id = todo["id"]

    def test_attach_tag(self, cli):
        result = run(
            cli,
            "todo",
            "attach-tag",
            str(TestE2ETagWorkflow.todo_id),
            str(TestE2ETagWorkflow.tag_id1),
        )
        assert result.exit_code == 0
        assert "attached" in result.output

    def test_todo_has_tag_after_attach(self, cli):
        data = run_json(cli, "todo", "get", str(TestE2ETagWorkflow.todo_id))
        tag_ids = [t["id"] for t in data["tags"]]
        assert TestE2ETagWorkflow.tag_id1 in tag_ids

    def test_detach_tag(self, cli):
        result = run(
            cli,
            "todo",
            "detach-tag",
            str(TestE2ETagWorkflow.todo_id),
            str(TestE2ETagWorkflow.tag_id1),
        )
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_todo_has_no_tag_after_detach(self, cli):
        data = run_json(cli, "todo", "get", str(TestE2ETagWorkflow.todo_id))
        assert data["tags"] == []

    def test_teardown(self, cli):
        run(cli, "todo", "delete", str(TestE2ETagWorkflow.todo_id), "--yes")
        run(cli, "user", "delete", str(TestE2ETagWorkflow.user_id), "--yes")
        run(cli, "tag", "delete", str(TestE2ETagWorkflow.tag_id1), "--yes")
        run(cli, "tag", "delete", str(TestE2ETagWorkflow.tag_id2), "--yes")


# ---------------------------------------------------------------------------
# 5. 오류 케이스
# ---------------------------------------------------------------------------


class TestE2EErrorCases:
    """존재하지 않는 리소스, 필드 누락, 잘못된 enum 값"""

    def test_get_nonexistent_user(self, cli):
        result = run(cli, "user", "get", "99999")
        assert result.exit_code == 1
        assert "404" in result.stderr

    def test_get_nonexistent_todo(self, cli):
        result = run(cli, "todo", "get", "99999")
        assert result.exit_code == 1
        assert "404" in result.stderr

    def test_get_nonexistent_comment(self, cli):
        result = run(cli, "comment", "get", "99999")
        assert result.exit_code == 1
        assert "404" in result.stderr

    def test_get_nonexistent_tag(self, cli):
        result = run(cli, "tag", "get", "99999")
        assert result.exit_code == 1
        assert "404" in result.stderr

    def test_update_user_no_fields(self, cli):
        result = run(cli, "user", "update", "1")
        assert result.exit_code == 1
        assert "Please specify at least one field" in result.stderr

    def test_update_todo_no_fields(self, cli):
        result = run(cli, "todo", "update", "1")
        assert result.exit_code == 1
        assert "Please specify at least one field" in result.stderr

    def test_update_tag_no_fields(self, cli):
        result = run(cli, "tag", "update", "1")
        assert result.exit_code == 1
        assert "Please specify at least one field" in result.stderr

    def test_list_todos_invalid_status(self, cli):
        result = run(cli, "todo", "list", "--status", "invalid_status")
        assert result.exit_code != 0

    def test_list_todos_invalid_priority(self, cli):
        result = run(cli, "todo", "list", "--priority", "urgent")
        assert result.exit_code != 0

    def test_todo_list_assignee_filter(self, cli):
        """assignee_id 필터가 실제 쿼리 파라미터로 전달되는지 확인."""
        data = run_json(cli, "todo", "list", "--assignee", "99999")
        assert data == []
