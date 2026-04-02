"""TC-CFG: 설정 관리 테스트 (HTTP 호출 없음)"""

import json

from ttodo.config import DEFAULT_SERVER
from ttodo.main import app


class TestConfigShow:
    def test_show_default_server_when_no_config(self, runner, mock_config):
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert DEFAULT_SERVER in result.output

    def test_show_custom_server_after_set(self, runner, mock_config):
        runner.invoke(app, ["config", "set-server", "http://192.168.1.100:8000"])
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "http://192.168.1.100:8000" in result.output

    def test_show_json_output(self, runner, mock_config):
        result = runner.invoke(app, ["--json", "config", "show"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "server_url" in data
        assert "config_file" in data
        assert data["server_url"] == DEFAULT_SERVER


class TestConfigSetServer:
    def test_set_server_prints_success_message(self, runner, mock_config):
        result = runner.invoke(app, ["config", "set-server", "http://10.0.0.1:8000"])
        assert result.exit_code == 0
        assert "http://10.0.0.1:8000" in result.output

    def test_set_server_saves_to_file(self, runner, mock_config):
        url = "http://10.0.0.1:8000"
        runner.invoke(app, ["config", "set-server", url])
        config_file = mock_config["file"]
        assert config_file.exists()
        content = config_file.read_text()
        assert url in content

    def test_set_server_overwrites_existing_url(self, runner, mock_config):
        runner.invoke(app, ["config", "set-server", "http://old:8000"])
        runner.invoke(app, ["config", "set-server", "http://new:8000"])
        result = runner.invoke(app, ["--json", "config", "show"])
        data = json.loads(result.output)
        assert data["server_url"] == "http://new:8000"


class TestConfigReset:
    def test_reset_with_yes_flag(self, runner, mock_config):
        runner.invoke(app, ["config", "set-server", "http://custom:8000"])
        result = runner.invoke(app, ["config", "reset", "--yes"])
        assert result.exit_code == 0
        assert DEFAULT_SERVER in result.output

    def test_reset_restores_default_server(self, runner, mock_config):
        runner.invoke(app, ["config", "set-server", "http://custom:8000"])
        runner.invoke(app, ["config", "reset", "--yes"])
        result = runner.invoke(app, ["--json", "config", "show"])
        data = json.loads(result.output)
        assert data["server_url"] == DEFAULT_SERVER

    def test_reset_prompt_confirm(self, runner, mock_config):
        runner.invoke(app, ["config", "set-server", "http://custom:8000"])
        result = runner.invoke(app, ["config", "reset"], input="y\n")
        assert result.exit_code == 0

    def test_reset_prompt_cancel(self, runner, mock_config):
        runner.invoke(app, ["config", "set-server", "http://custom:8000"])
        result = runner.invoke(app, ["config", "reset"], input="n\n")
        assert result.exit_code == 1
        result2 = runner.invoke(app, ["--json", "config", "show"])
        data = json.loads(result2.output)
        assert data["server_url"] == "http://custom:8000"
