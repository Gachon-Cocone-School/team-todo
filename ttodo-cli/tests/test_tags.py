"""TC-TAG: 태그 관리 테스트"""

import json

import httpx
from ttodo.main import app

from tests.fixtures.responses import DELETED, NOT_FOUND, TAG, TAG_LIST, TAG_NO_COLOR


class TestTagList:
    def test_list_table_output(self, runner, mock_server):
        mock_server.get("http://testserver/tags").mock(
            return_value=httpx.Response(200, json=TAG_LIST)
        )
        result = runner.invoke(app, ["tag", "list"])
        assert result.exit_code == 0
        assert "버그" in result.output

    def test_list_json_output(self, runner, mock_server):
        mock_server.get("http://testserver/tags").mock(
            return_value=httpx.Response(200, json=TAG_LIST)
        )
        result = runner.invoke(app, ["--json", "tag", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 2

    def test_list_empty_result(self, runner, mock_server):
        mock_server.get("http://testserver/tags").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = runner.invoke(app, ["tag", "list"])
        assert result.exit_code == 0
        assert "결과 없음" in result.output


class TestTagCreate:
    def test_create_name_only(self, runner, mock_server):
        mock_server.post("http://testserver/tags").mock(
            return_value=httpx.Response(201, json=TAG_NO_COLOR)
        )
        result = runner.invoke(app, ["tag", "create", "--name", "리뷰"])
        assert result.exit_code == 0
        assert "Tag created" in result.output

    def test_create_with_color(self, runner, mock_server):
        mock_server.post("http://testserver/tags").mock(
            return_value=httpx.Response(201, json=TAG)
        )
        result = runner.invoke(
            app, ["tag", "create", "--name", "버그", "--color", "#ff0000"]
        )
        assert result.exit_code == 0

    def test_create_short_options(self, runner, mock_server):
        mock_server.post("http://testserver/tags").mock(
            return_value=httpx.Response(201, json=TAG)
        )
        result = runner.invoke(app, ["tag", "create", "-n", "버그", "-c", "#ff0000"])
        assert result.exit_code == 0

    def test_create_json_output(self, runner, mock_server):
        mock_server.post("http://testserver/tags").mock(
            return_value=httpx.Response(201, json=TAG)
        )
        result = runner.invoke(app, ["--json", "tag", "create", "--name", "버그"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == 1

    def test_create_missing_name(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["tag", "create"])
        assert result.exit_code != 0


class TestTagGet:
    def test_get_success(self, runner, mock_server):
        mock_server.get("http://testserver/tags/1").mock(
            return_value=httpx.Response(200, json=TAG)
        )
        result = runner.invoke(app, ["tag", "get", "1"])
        assert result.exit_code == 0
        assert "버그" in result.output

    def test_get_json_output(self, runner, mock_server):
        mock_server.get("http://testserver/tags/1").mock(
            return_value=httpx.Response(200, json=TAG)
        )
        result = runner.invoke(app, ["--json", "tag", "get", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["name"] == "버그"
        assert data["color"] == "#ff0000"

    def test_get_not_found(self, runner, mock_server):
        mock_server.get("http://testserver/tags/999").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["tag", "get", "999"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr


class TestTagUpdate:
    def test_update_name(self, runner, mock_server):
        updated = {**TAG, "name": "버그수정"}
        mock_server.put("http://testserver/tags/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(app, ["tag", "update", "1", "--name", "버그수정"])
        assert result.exit_code == 0
        assert "Tag updated" in result.output

    def test_update_color(self, runner, mock_server):
        updated = {**TAG, "color": "#0000ff"}
        mock_server.put("http://testserver/tags/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(app, ["tag", "update", "1", "--color", "#0000ff"])
        assert result.exit_code == 0

    def test_update_both_fields(self, runner, mock_server):
        updated = {**TAG, "name": "긴급버그", "color": "#ff4444"}
        mock_server.put("http://testserver/tags/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(
            app, ["tag", "update", "1", "--name", "긴급버그", "--color", "#ff4444"]
        )
        assert result.exit_code == 0
        assert "Tag updated" in result.output

    def test_update_short_options(self, runner, mock_server):
        updated = {**TAG, "name": "새태그"}
        mock_server.put("http://testserver/tags/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(
            app, ["tag", "update", "1", "-n", "새태그", "-c", "#ffffff"]
        )
        assert result.exit_code == 0

    def test_update_no_fields(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["tag", "update", "1"])
        assert result.exit_code == 1
        assert "Please specify at least one field" in result.stderr

    def test_update_not_found(self, runner, mock_server):
        mock_server.put("http://testserver/tags/999").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["tag", "update", "999", "--name", "테스트"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr


class TestTagDelete:
    def test_delete_with_yes_flag(self, runner, mock_server):
        mock_server.delete("http://testserver/tags/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["tag", "delete", "1", "--yes"])
        assert result.exit_code == 0
        assert "deleted." in result.output

    def test_delete_with_short_yes_flag(self, runner, mock_server):
        mock_server.delete("http://testserver/tags/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["tag", "delete", "1", "-y"])
        assert result.exit_code == 0

    def test_delete_prompt_confirm(self, runner, mock_server):
        mock_server.delete("http://testserver/tags/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["tag", "delete", "1"], input="y\n")
        assert result.exit_code == 0

    def test_delete_prompt_cancel(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["tag", "delete", "1"], input="n\n")
        assert result.exit_code == 1
