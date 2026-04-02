"""TC-G: 전역 옵션 테스트 (--json 플래그)"""

import json

import httpx
from ttodo.main import app

from tests.fixtures.responses import COMMENT, TAG, TODO, USER, USER_LIST


class TestJsonFlag:
    def test_user_list_json(self, runner, mock_server):
        mock_server.get("http://testserver/users").mock(
            return_value=httpx.Response(200, json=USER_LIST)
        )
        result = runner.invoke(app, ["--json", "user", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_user_get_json(self, runner, mock_server):
        mock_server.get("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=USER)
        )
        result = runner.invoke(app, ["--json", "user", "get", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        assert data["id"] == 1

    def test_todo_list_json(self, runner, mock_server):
        mock_server.get("http://testserver/todos").mock(
            return_value=httpx.Response(200, json=[TODO])
        )
        result = runner.invoke(app, ["--json", "todo", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_todo_get_json(self, runner, mock_server):
        mock_server.get("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=TODO)
        )
        result = runner.invoke(app, ["--json", "todo", "get", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["title"] == "테스트 할일"

    def test_tag_list_json(self, runner, mock_server):
        mock_server.get("http://testserver/tags").mock(
            return_value=httpx.Response(200, json=[TAG])
        )
        result = runner.invoke(app, ["--json", "tag", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data[0]["name"] == "버그"

    def test_comment_get_json(self, runner, mock_server):
        mock_server.get("http://testserver/comments/1").mock(
            return_value=httpx.Response(200, json=COMMENT)
        )
        result = runner.invoke(app, ["--json", "comment", "get", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["content"] == "댓글 내용입니다"

    def test_json_flag_with_filter(self, runner, mock_server):
        mock_server.get("http://testserver/todos", params={"status": "done"}).mock(
            return_value=httpx.Response(200, json=[TODO])
        )
        result = runner.invoke(app, ["--json", "todo", "list", "--status", "done"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
