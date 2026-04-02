"""TC-E: 에러 처리 테스트"""

import httpx
import respx
from ttodo.main import app


class TestConnectionErrors:
    def test_connect_error_shows_message(self, runner, mock_config_with_server):
        with respx.mock:
            respx.get("http://testserver/users").mock(
                side_effect=httpx.ConnectError("연결 실패")
            )
            result = runner.invoke(app, ["user", "list"])
        assert result.exit_code == 1
        assert "서버 연결 실패" in result.stderr

    def test_connect_error_shows_server_url(self, runner, mock_config_with_server):
        with respx.mock:
            respx.get("http://testserver/users").mock(
                side_effect=httpx.ConnectError("연결 실패")
            )
            result = runner.invoke(app, ["user", "list"])
        assert "http://testserver" in result.stderr

    def test_connect_error_suggests_config_show(self, runner, mock_config_with_server):
        with respx.mock:
            respx.get("http://testserver/users").mock(
                side_effect=httpx.ConnectError("연결 실패")
            )
            result = runner.invoke(app, ["user", "list"])
        assert "ttodo config show" in result.stderr

    def test_timeout_error_shows_message(self, runner, mock_config_with_server):
        with respx.mock:
            respx.get("http://testserver/users").mock(
                side_effect=httpx.TimeoutException("타임아웃")
            )
            result = runner.invoke(app, ["user", "list"])
        assert result.exit_code == 1
        assert "시간 초과" in result.stderr


class TestInvalidInput:
    def test_invalid_user_id_type(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["user", "get", "abc"])
        assert result.exit_code != 0

    def test_invalid_todo_id_type(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["todo", "get", "abc"])
        assert result.exit_code != 0

    def test_invalid_comment_id_type(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["comment", "get", "abc"])
        assert result.exit_code != 0

    def test_invalid_tag_id_type(self, runner, mock_config_with_server):
        result = runner.invoke(app, ["tag", "get", "abc"])
        assert result.exit_code != 0

    def test_http_400_shows_error(self, runner, mock_server):
        mock_server.post("http://testserver/users").mock(
            return_value=httpx.Response(400, json={"detail": "잘못된 요청"})
        )
        result = runner.invoke(
            app, ["user", "create", "--name", "테스트", "--email", "test@test.com"]
        )
        assert result.exit_code == 1
        assert "오류 400" in result.stderr

    def test_http_422_shows_error(self, runner, mock_server):
        mock_server.post("http://testserver/todos").mock(
            return_value=httpx.Response(
                422, json={"detail": [{"msg": "field required"}]}
            )
        )
        result = runner.invoke(
            app, ["todo", "create", "--title", "테스트", "--created-by", "1"]
        )
        assert result.exit_code == 1
        assert "오류 422" in result.stderr
