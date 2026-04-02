"""TC-T: 할일 관리 테스트"""

import json

import httpx
from ttodo.main import app

from tests.fixtures.responses import (
    ATTACHED,
    DELETED,
    DETACHED,
    NOT_FOUND,
    TODO,
    TODO_IN_PROGRESS,
    TODO_LIST,
    TODO_WITH_TAGS,
)


class TestTodoList:
    def test_list_all_table_output(self, runner, mock_server):
        mock_server.get("http://testserver/todos").mock(
            return_value=httpx.Response(200, json=TODO_LIST)
        )
        result = runner.invoke(app, ["todo", "list"])
        assert result.exit_code == 0
        assert "테스트 할일" in result.output

    def test_list_all_json_output(self, runner, mock_server):
        mock_server.get("http://testserver/todos").mock(
            return_value=httpx.Response(200, json=TODO_LIST)
        )
        result = runner.invoke(app, ["--json", "todo", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 2

    def test_list_empty_result(self, runner, mock_server):
        mock_server.get("http://testserver/todos").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = runner.invoke(app, ["todo", "list"])
        assert result.exit_code == 0
        assert "결과 없음" in result.output

    def test_list_with_status_filter(self, runner, mock_server):
        mock_server.get("http://testserver/todos", params={"status": "todo"}).mock(
            return_value=httpx.Response(200, json=[TODO])
        )
        result = runner.invoke(app, ["todo", "list", "--status", "todo"])
        assert result.exit_code == 0

    def test_list_with_priority_filter(self, runner, mock_server):
        mock_server.get("http://testserver/todos", params={"priority": "high"}).mock(
            return_value=httpx.Response(200, json=[TODO_IN_PROGRESS])
        )
        result = runner.invoke(app, ["todo", "list", "--priority", "high"])
        assert result.exit_code == 0

    def test_list_with_assignee_filter(self, runner, mock_server):
        mock_server.get("http://testserver/todos", params={"assignee_id": "1"}).mock(
            return_value=httpx.Response(200, json=[TODO])
        )
        result = runner.invoke(app, ["todo", "list", "--assignee", "1"])
        assert result.exit_code == 0

    def test_list_with_tag_filter(self, runner, mock_server):
        mock_server.get("http://testserver/todos", params={"tag_id": "2"}).mock(
            return_value=httpx.Response(200, json=[TODO])
        )
        result = runner.invoke(app, ["todo", "list", "--tag", "2"])
        assert result.exit_code == 0

    def test_list_combined_filters(self, runner, mock_server):
        mock_server.get(
            "http://testserver/todos",
            params={"status": "todo", "priority": "high"},
        ).mock(return_value=httpx.Response(200, json=[TODO]))
        result = runner.invoke(
            app, ["todo", "list", "--status", "todo", "--priority", "high"]
        )
        assert result.exit_code == 0

    def test_list_combined_filters_with_short_options(self, runner, mock_server):
        mock_server.get(
            "http://testserver/todos",
            params={"status": "in_progress", "priority": "low"},
        ).mock(return_value=httpx.Response(200, json=[TODO_IN_PROGRESS]))
        result = runner.invoke(app, ["todo", "list", "-s", "in_progress", "-p", "low"])
        assert result.exit_code == 0

    def test_list_short_assignee_option(self, runner, mock_server):
        mock_server.get("http://testserver/todos", params={"assignee_id": "1"}).mock(
            return_value=httpx.Response(200, json=[TODO])
        )
        result = runner.invoke(app, ["todo", "list", "-a", "1"])
        assert result.exit_code == 0

    def test_list_short_tag_option(self, runner, mock_server):
        mock_server.get("http://testserver/todos", params={"tag_id": "2"}).mock(
            return_value=httpx.Response(200, json=[TODO])
        )
        result = runner.invoke(app, ["todo", "list", "-t", "2"])
        assert result.exit_code == 0

    def test_list_invalid_status_value(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["todo", "list", "--status", "invalid"])
        assert result.exit_code != 0

    def test_list_invalid_priority_value(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["todo", "list", "--priority", "urgent"])
        assert result.exit_code != 0


class TestTodoCreate:
    def test_create_minimal(self, runner, mock_server):
        mock_server.post("http://testserver/todos").mock(
            return_value=httpx.Response(201, json=TODO)
        )
        result = runner.invoke(
            app, ["todo", "create", "--title", "테스트 할일", "--created-by", "1"]
        )
        assert result.exit_code == 0
        assert "Todo created" in result.output

    def test_create_all_options(self, runner, mock_server):
        mock_server.post("http://testserver/todos").mock(
            return_value=httpx.Response(201, json=TODO)
        )
        result = runner.invoke(
            app,
            [
                "todo",
                "create",
                "--title",
                "전체 옵션 할일",
                "--created-by",
                "1",
                "--description",
                "설명",
                "--status",
                "in_progress",
                "--priority",
                "high",
                "--due-date",
                "2026-04-30",
                "--assignee",
                "2",
            ],
        )
        assert result.exit_code == 0

    def test_create_json_output(self, runner, mock_server):
        mock_server.post("http://testserver/todos").mock(
            return_value=httpx.Response(201, json=TODO)
        )
        result = runner.invoke(
            app, ["--json", "todo", "create", "--title", "테스트", "--created-by", "1"]
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == 1

    def test_create_short_options(self, runner, mock_server):
        mock_server.post("http://testserver/todos").mock(
            return_value=httpx.Response(201, json=TODO)
        )
        result = runner.invoke(
            app,
            [
                "todo",
                "create",
                "--title",
                "단축 옵션 할일",
                "--created-by",
                "1",
                "-d",
                "설명",
                "-s",
                "in_progress",
                "-p",
                "high",
                "-a",
                "2",
            ],
        )
        assert result.exit_code == 0

    def test_create_missing_title(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["todo", "create", "--created-by", "1"])
        assert result.exit_code != 0

    def test_create_missing_created_by(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["todo", "create", "--title", "테스트"])
        assert result.exit_code != 0


class TestTodoGet:
    def test_get_success(self, runner, mock_server):
        mock_server.get("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=TODO)
        )
        result = runner.invoke(app, ["todo", "get", "1"])
        assert result.exit_code == 0
        assert "테스트 할일" in result.output

    def test_get_with_tags(self, runner, mock_server):
        mock_server.get("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=TODO_WITH_TAGS)
        )
        result = runner.invoke(app, ["todo", "get", "1"])
        assert result.exit_code == 0
        assert "버그" in result.output

    def test_get_json_output(self, runner, mock_server):
        mock_server.get("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=TODO_WITH_TAGS)
        )
        result = runner.invoke(app, ["--json", "todo", "get", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["tags"][0]["name"] == "버그"

    def test_get_not_found(self, runner, mock_server):
        mock_server.get("http://testserver/todos/999").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["todo", "get", "999"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr


class TestTodoUpdate:
    def test_update_status(self, runner, mock_server):
        updated = {**TODO, "status": "done"}
        mock_server.put("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(app, ["todo", "update", "1", "--status", "done"])
        assert result.exit_code == 0
        assert "Todo updated" in result.output

    def test_update_priority(self, runner, mock_server):
        updated = {**TODO, "priority": "low"}
        mock_server.put("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(app, ["todo", "update", "1", "--priority", "low"])
        assert result.exit_code == 0

    def test_update_multiple_fields(self, runner, mock_server):
        updated = {
            **TODO,
            "priority": "low",
            "assignee_id": 2,
            "due_date": "2026-05-01",
        }
        mock_server.put("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(
            app,
            [
                "todo",
                "update",
                "1",
                "--priority",
                "low",
                "--assignee",
                "2",
                "--due-date",
                "2026-05-01",
            ],
        )
        assert result.exit_code == 0
        assert "Todo updated" in result.output

    def test_update_short_options(self, runner, mock_server):
        updated = {**TODO, "status": "done", "priority": "high"}
        mock_server.put("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(app, ["todo", "update", "1", "-s", "done", "-p", "high"])
        assert result.exit_code == 0

    def test_update_title_and_description(self, runner, mock_server):
        updated = {**TODO, "title": "수정된 제목", "description": "수정된 설명"}
        mock_server.put("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=updated)
        )
        result = runner.invoke(
            app, ["todo", "update", "1", "--title", "수정된 제목", "-d", "수정된 설명"]
        )
        assert result.exit_code == 0

    def test_update_no_fields(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["todo", "update", "1"])
        assert result.exit_code == 1
        assert "Please specify at least one field" in result.stderr

    def test_update_not_found(self, runner, mock_server):
        mock_server.put("http://testserver/todos/999").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["todo", "update", "999", "--status", "done"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr


class TestTodoDelete:
    def test_delete_with_yes_flag(self, runner, mock_server):
        mock_server.delete("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["todo", "delete", "1", "--yes"])
        assert result.exit_code == 0
        assert "deleted." in result.output

    def test_delete_with_short_yes_flag(self, runner, mock_server):
        mock_server.delete("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["todo", "delete", "1", "-y"])
        assert result.exit_code == 0

    def test_delete_prompt_confirm(self, runner, mock_server):
        mock_server.delete("http://testserver/todos/1").mock(
            return_value=httpx.Response(200, json=DELETED)
        )
        result = runner.invoke(app, ["todo", "delete", "1"], input="y\n")
        assert result.exit_code == 0

    def test_delete_prompt_cancel(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["todo", "delete", "1"], input="n\n")
        assert result.exit_code == 1


class TestTodoTags:
    def test_attach_tag_success(self, runner, mock_server):
        mock_server.post("http://testserver/todos/1/tags/2").mock(
            return_value=httpx.Response(200, json=ATTACHED)
        )
        result = runner.invoke(app, ["todo", "attach-tag", "1", "2"])
        assert result.exit_code == 0
        assert "attached" in result.output

    def test_detach_tag_success(self, runner, mock_server):
        mock_server.delete("http://testserver/todos/1/tags/2").mock(
            return_value=httpx.Response(200, json=DETACHED)
        )
        result = runner.invoke(app, ["todo", "detach-tag", "1", "2"])
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_attach_tag_todo_not_found(self, runner, mock_server):
        mock_server.post("http://testserver/todos/999/tags/1").mock(
            return_value=httpx.Response(404, json=NOT_FOUND)
        )
        result = runner.invoke(app, ["todo", "attach-tag", "999", "1"])
        assert result.exit_code == 1
        assert "오류 404" in result.stderr
