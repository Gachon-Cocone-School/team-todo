"""TC-C: 댓글 관리 테스트"""

import json

import httpx
from ttodo.main import app

from tests.fixtures.responses import COMMENT, COMMENT_LIST, DELETED, NOT_FOUND


class TestCommentList:
    def test_list_comments_success(self, runner, mock_server):
        mock_server.get("http://testserver/todos/1/comments").mock(
            return_value=httpx.Response(200, json=COMMENT_LIST)
        )
        result = runner.invoke(app, ["comment", "list", "1"])
        assert result.exit_code == 0
        assert "댓글 내용입니다" in result.output

    def test_list_comments_json_output(self, runner, mock_server):
        mock_server.get("http://testserver/todos/1/comments").mock(
            return_value=httpx.Response(200, json=COMMENT_LIST)
        )
        result = runner.invoke(app, ["--json", "comment", "list", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["content"] == "댓글 내용입니다"

    def test_list_comments_empty(self, runner, mock_server):
        mock_server.get("http://testserver/todos/1/comments").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = runner.invoke(app, ["comment", "list", "1"])
        assert result.exit_code == 0
        assert "결과 없음" in result.output

    def test_list_comments_todo_not_found(self, runner, mock_server):
        mock_server.get("http://testserver/todos/999/comments").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["comment", "list", "999"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr


class TestCommentCreate:
    def test_create_success(self, runner, mock_server):
        mock_server.post("http://testserver/todos/1/comments").mock(
            return_value=httpx.Response(201, json=COMMENT)
        )
        result = runner.invoke(
            app, ["comment", "create", "1", "--author", "1", "--content", "새 댓글"]
        )
        assert result.exit_code == 0
        assert "Comment posted" in result.output

    def test_create_short_options(self, runner, mock_server):
        mock_server.post("http://testserver/todos/1/comments").mock(
            return_value=httpx.Response(201, json=COMMENT)
        )
        result = runner.invoke(
            app, ["comment", "create", "1", "-a", "1", "-c", "새 댓글"]
        )
        assert result.exit_code == 0

    def test_create_json_output(self, runner, mock_server):
        mock_server.post("http://testserver/todos/1/comments").mock(
            return_value=httpx.Response(201, json=COMMENT)
        )
        result = runner.invoke(
            app,
            [
                "--json",
                "comment",
                "create",
                "1",
                "--author",
                "1",
                "--content",
                "새 댓글",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == 1

    def test_create_todo_not_found(self, runner, mock_server):
        mock_server.post("http://testserver/todos/999/comments").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(
            app, ["comment", "create", "999", "--author", "1", "--content", "새 댓글"]
        )
        assert result.exit_code == 1
        assert "오류 404" in result.stderr

    def test_create_missing_author(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["comment", "create", "1", "--content", "새 댓글"])
        assert result.exit_code != 0

    def test_create_missing_content(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["comment", "create", "1", "--author", "1"])
        assert result.exit_code != 0


class TestCommentGet:
    def test_get_success(self, runner, mock_server):
        mock_server.get("http://testserver/comments/1").mock(
            return_value=httpx.Response(200, json=COMMENT)
        )
        result = runner.invoke(app, ["comment", "get", "1"])
        assert result.exit_code == 0
        assert "댓글 내용입니다" in result.output

    def test_get_json_output(self, runner, mock_server):
        mock_server.get("http://testserver/comments/1").mock(
            return_value=httpx.Response(200, json=COMMENT)
        )
        result = runner.invoke(app, ["--json", "comment", "get", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["todo_id"] == 1
        assert data["author_id"] == 1

    def test_get_not_found(self, runner, mock_server):
        mock_server.get("http://testserver/comments/999").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["comment", "get", "999"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr


class TestCommentUpdate:
    def test_update_success(self, runner, mock_server):
        updated = {**COMMENT, "content": "수정된 댓글"}
        mock_server.put("http://testserver/comments/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(
            app, ["comment", "update", "1", "--content", "수정된 댓글"]
        )
        assert result.exit_code == 0
        assert "Comment updated" in result.output

    def test_update_short_option(self, runner, mock_server):
        updated = {**COMMENT, "content": "수정"}
        mock_server.put("http://testserver/comments/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(app, ["comment", "update", "1", "-c", "수정"])
        assert result.exit_code == 0

    def test_update_not_found(self, runner, mock_server):
        mock_server.put("http://testserver/comments/999").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["comment", "update", "999", "--content", "수정"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr


class TestCommentDelete:
    def test_delete_with_yes_flag(self, runner, mock_server):
        mock_server.delete("http://testserver/comments/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["comment", "delete", "1", "--yes"])
        assert result.exit_code == 0
        assert "deleted." in result.output

    def test_delete_with_short_yes_flag(self, runner, mock_server):
        mock_server.delete("http://testserver/comments/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["comment", "delete", "1", "-y"])
        assert result.exit_code == 0

    def test_delete_prompt_confirm(self, runner, mock_server):
        mock_server.delete("http://testserver/comments/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["comment", "delete", "1"], input="y\n")
        assert result.exit_code == 0

    def test_delete_prompt_cancel(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["comment", "delete", "1"], input="n\n")
        assert result.exit_code == 1
