"""TC-U: 유저 관리 테스트"""

import json

import httpx
from ttodo.main import app

from tests.fixtures.responses import DELETED, NOT_FOUND, USER, USER_LIST


class TestUserList:
    def test_list_table_output(self, runner, mock_server):
        mock_server.get("http://testserver/users").mock(
            return_value=httpx.Response(200, json=USER_LIST)
        )
        result = runner.invoke(app, ["user", "list"])
        assert result.exit_code == 0
        assert "홍길동" in result.output

    def test_list_json_output(self, runner, mock_server):
        mock_server.get("http://testserver/users").mock(
            return_value=httpx.Response(200, json=USER_LIST)
        )
        result = runner.invoke(app, ["--json", "user", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 2
        assert data[0]["name"] == "홍길동"

    def test_list_empty_result(self, runner, mock_server):
        mock_server.get("http://testserver/users").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = runner.invoke(app, ["user", "list"])
        assert result.exit_code == 0
        assert "결과 없음" in result.output


class TestUserCreate:
    def test_create_success(self, runner, mock_server):
        mock_server.post("http://testserver/users").mock(
            return_value=httpx.Response(201, json=USER)
        )
        result = runner.invoke(
            app, ["user", "create", "--name", "홍길동", "--email", "hong@example.com"]
        )
        assert result.exit_code == 0
        assert "Team member created" in result.output
        assert "1" in result.output

    def test_create_json_output(self, runner, mock_server):
        mock_server.post("http://testserver/users").mock(
            return_value=httpx.Response(201, json=USER)
        )
        result = runner.invoke(
            app,
            [
                "--json",
                "user",
                "create",
                "--name",
                "홍길동",
                "--email",
                "hong@example.com",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["name"] == "홍길동"

    def test_create_short_options(self, runner, mock_server):
        mock_server.post("http://testserver/users").mock(
            return_value=httpx.Response(201, json=USER)
        )
        result = runner.invoke(
            app, ["user", "create", "-n", "홍길동", "-e", "hong@example.com"]
        )
        assert result.exit_code == 0

    def test_create_missing_name(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["user", "create", "--email", "hong@example.com"])
        assert result.exit_code != 0

    def test_create_missing_email(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["user", "create", "--name", "홍길동"])
        assert result.exit_code != 0


class TestUserGet:
    def test_get_success(self, runner, mock_server):
        mock_server.get("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=USER)
        )
        result = runner.invoke(app, ["user", "get", "1"])
        assert result.exit_code == 0
        assert "홍길동" in result.output

    def test_get_json_output(self, runner, mock_server):
        mock_server.get("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=USER)
        )
        result = runner.invoke(app, ["--json", "user", "get", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == 1
        assert data["email"] == "hong@example.com"

    def test_get_not_found(self, runner, mock_server):
        mock_server.get("http://testserver/users/999").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["user", "get", "999"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr

    def test_get_invalid_id_type(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["user", "get", "abc"])
        assert result.exit_code != 0


class TestUserUpdate:
    def test_update_name_only(self, runner, mock_server):
        updated = {**USER, "name": "홍길동2"}
        mock_server.put("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(app, ["user", "update", "1", "--name", "홍길동2"])
        assert result.exit_code == 0
        assert "Team member updated" in result.output

    def test_update_email_only(self, runner, mock_server):
        updated = {**USER, "email": "new@example.com"}
        mock_server.put("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(
            app, ["user", "update", "1", "--email", "new@example.com"]
        )
        assert result.exit_code == 0

    def test_update_json_output(self, runner, mock_server):
        updated = {**USER, "name": "홍길동2"}
        mock_server.put("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(
            app, ["--json", "user", "update", "1", "--name", "홍길동2"]
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["name"] == "홍길동2"

    def test_update_both_fields(self, runner, mock_server):
        updated = {**USER, "name": "홍길동2", "email": "new@example.com"}
        mock_server.put("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(
            app,
            ["user", "update", "1", "--name", "홍길동2", "--email", "new@example.com"],
        )
        assert result.exit_code == 0
        assert "Team member updated" in result.output

    def test_update_short_options(self, runner, mock_server):
        updated = {**USER, "name": "홍길동2"}
        mock_server.put("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(app, ["user", "update", "1", "-n", "홍길동2"])
        assert result.exit_code == 0

    def test_update_no_fields(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["user", "update", "1"])
        assert result.exit_code == 1
        assert "Please specify at least one field" in result.stderr

    def test_update_not_found(self, runner, mock_server):
        mock_server.put("http://testserver/users/999").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["user", "update", "999", "--name", "테스트"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr


class TestUserDelete:
    def test_delete_with_yes_flag(self, runner, mock_server):
        mock_server.delete("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["user", "delete", "1", "--yes"])
        assert result.exit_code == 0
        assert "deleted." in result.output

    def test_delete_with_short_yes_flag(self, runner, mock_server):
        mock_server.delete("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["user", "delete", "1", "-y"])
        assert result.exit_code == 0

    def test_delete_prompt_confirm(self, runner, mock_server):
        mock_server.delete("http://testserver/users/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["user", "delete", "1"], input="y\n")
        assert result.exit_code == 0

    def test_delete_prompt_cancel(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["user", "delete", "1"], input="n\n")
        assert result.exit_code == 1

    def test_delete_not_found(self, runner, mock_server):
        mock_server.delete("http://testserver/users/999").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["user", "delete", "999", "--yes"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr
