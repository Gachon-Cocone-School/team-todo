"""E2E 테스트 픽스처 — 실제 uvicorn 서버를 subprocess로 기동한다."""

import json
import os
import socket
import subprocess
import time
from pathlib import Path

import httpx
import pytest
import ttodo.config as config_module
import ttodo.state as state_module
from typer.testing import CliRunner

# team-todo/ 프로젝트 루트 (ttodo-cli/tests/e2e/ 에서 4단계 상위)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def _free_port() -> int:
    """사용 가능한 임의 포트를 반환한다."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_ready(url: str, timeout: float = 10.0) -> None:
    """서버가 응답할 때까지 최대 timeout 초 동안 대기한다."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            httpx.get(f"{url}/users", timeout=0.5)
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"E2E 서버가 {timeout}초 내에 기동되지 않았습니다: {url}")


@pytest.fixture(scope="session")
def e2e_server(tmp_path_factory):
    """임시 SQLite DB로 uvicorn 서버를 기동하고 URL을 반환한다."""
    db_file = tmp_path_factory.mktemp("e2e_db") / "test.db"
    port = _free_port()
    server_url = f"http://127.0.0.1:{port}"

    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_file}"}
    proc = subprocess.Popen(
        [
            "uv",
            "run",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "error",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_ready(server_url)
    except RuntimeError:
        proc.terminate()
        proc.wait()
        raise

    yield server_url

    proc.terminate()
    proc.wait()


@pytest.fixture
def cli(e2e_server, tmp_path, monkeypatch):
    """실서버를 가리키는 config로 설정된 CliRunner를 반환한다."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(f'[server]\nurl = "{e2e_server}"\n', encoding="utf-8")
    monkeypatch.setattr(config_module, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
    state_module.state.json_output = False
    return CliRunner(env={"NO_COLOR": "1", "COLUMNS": "200"})


@pytest.fixture
def json_cli(e2e_server, tmp_path, monkeypatch):
    """--json 출력용 CliRunner (cli fixture와 동일한 config)."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(f'[server]\nurl = "{e2e_server}"\n', encoding="utf-8")
    monkeypatch.setattr(config_module, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
    state_module.state.json_output = False
    return CliRunner(env={"NO_COLOR": "1", "COLUMNS": "200"})


def invoke_json(runner: CliRunner, args: list) -> dict | list:
    """--json 플래그를 붙여 CLI를 실행하고 파싱된 JSON을 반환한다."""
    from ttodo.main import app

    result = runner.invoke(app, ["--json"] + args)
    assert result.exit_code == 0, (
        f"CLI 실패: {result.output}\n{result.stderr if hasattr(result, 'stderr') else ''}"
    )
    return json.loads(result.stdout)
