import tomllib
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "ttodo"
CONFIG_FILE = CONFIG_DIR / "config.toml"
DEFAULT_SERVER = "http://localhost:8000"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for section, values in config.items():
        lines.append(f"[{section}]")
        for key, value in values.items():
            lines.append(f'{key} = "{value}"')
        lines.append("")
    CONFIG_FILE.write_text("\n".join(lines), encoding="utf-8")


def get_server_url() -> str:
    config = load_config()
    return config.get("server", {}).get("url", DEFAULT_SERVER)
