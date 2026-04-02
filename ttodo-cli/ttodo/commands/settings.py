import typer

from ttodo.config import (
    CONFIG_FILE,
    DEFAULT_SERVER,
    get_server_url,
    load_config,
    save_config,
)
from ttodo.output import print_json, print_record
from ttodo.state import state

app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Configure the connection to your ttodo server.\n\n"
        "Before using other commands, you need to point ttodo at your server.\n"
        "Run 'ttodo config set-server <url>' to get started.\n\n"
        "Examples:\n\n"
        "  ttodo config show\n\n"
        "  ttodo config set-server http://192.168.1.100:8000\n\n"
        "  ttodo config reset"
    ),
)


@app.command(
    "show",
    help="Show the current server URL and the location of the config file.",
    epilog="Example:  ttodo config show",
)
def show_config() -> None:
    server_url = get_server_url()
    config_path = str(CONFIG_FILE)
    if state.json_output:
        print_json({"server_url": server_url, "config_file": config_path})
    else:
        print_record(
            "ttodo Settings",
            {
                "Server URL": server_url,
                "Config File": config_path,
            },
        )


@app.command(
    "set-server",
    help=(
        "Set the URL of the ttodo server.\n\n"
        "Use this command once to tell ttodo where your server is running.\n"
        "The URL is saved to a config file and used for all future commands."
    ),
    epilog=(
        "Examples:\n\n"
        "  ttodo config set-server http://localhost:8000\n\n"
        "  ttodo config set-server http://192.168.1.100:8000"
    ),
)
def set_server(
    url: str = typer.Argument(
        ...,
        help="The full URL of the server  (e.g. http://192.168.1.100:8000)",
    ),
) -> None:
    config = load_config()
    config.setdefault("server", {})["url"] = url
    save_config(config)
    typer.echo(f"Server URL saved: {url}")


@app.command(
    "reset",
    help=(
        "Reset the server URL back to the default.\n\n"
        f"The default server is: {DEFAULT_SERVER}\n\n"
        "Use --yes to skip the confirmation prompt."
    ),
    epilog=("Examples:\n\n  ttodo config reset\n\n  ttodo config reset --yes"),
)
def reset_config(
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip the confirmation prompt and reset immediately.",
    ),
) -> None:
    if not yes:
        typer.confirm("Reset settings to defaults?", abort=True)
    save_config({"server": {"url": DEFAULT_SERVER}})
    typer.echo(f"Settings reset. Server URL: {DEFAULT_SERVER}")
