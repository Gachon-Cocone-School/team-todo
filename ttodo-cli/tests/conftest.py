import pytest
import respx
import ttodo.config as config_module
import ttodo.state as state_module
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(env={"NO_COLOR": "1", "COLUMNS": "120"})


@pytest.fixture(autouse=True)
def reset_state() -> None:
    state_module.state.json_output = False
    yield
    state_module.state.json_output = False


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    fake_dir = tmp_path / "ttodo"
    fake_file = fake_dir / "config.toml"
    monkeypatch.setattr(config_module, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", fake_file)
    return {"dir": fake_dir, "file": fake_file}


@pytest.fixture
def mock_config_with_server(mock_config):
    config_module.save_config({"server": {"url": "http://testserver"}})
    return mock_config


@pytest.fixture
def mock_server(mock_config_with_server):
    with respx.mock(assert_all_called=False) as mock:
        yield mock
