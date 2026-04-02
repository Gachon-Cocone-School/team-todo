import typer

from ttodo.client import api_call
from ttodo.output import print_json, print_record, print_table
from ttodo.state import state

app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Create and manage tags to organize todos.\n\n"
        "Tags are labels you can attach to todos to group or categorize them.\n"
        "For example: 'bug', 'feature', 'urgent', 'design'.\n"
        "Each tag can optionally have a color in hex format (e.g. #ff0000 for red).\n\n"
        "Examples:\n\n"
        "  ttodo tag list\n\n"
        "  ttodo tag create --name 'bug' --color '#ff0000'\n\n"
        "  ttodo tag delete 2 --yes"
    ),
)


@app.command(
    "list",
    help="Show all available tags.",
    epilog="Example:  ttodo tag list",
)
def list_tags() -> None:
    data = api_call("GET", "/tags")
    if state.json_output:
        print_json(data)
    else:
        print_table(
            "Tags",
            ["ID", "Name", "Color"],
            [[t["id"], t["name"], t["color"]] for t in data],
        )


@app.command(
    "create",
    help=(
        "Create a new tag.\n\n"
        "Only --name is required. You can optionally set a color in hex format."
    ),
    epilog=(
        "Examples:\n\n"
        "  ttodo tag create --name 'bug'\n\n"
        "  ttodo tag create --name 'urgent' --color '#ff0000'\n\n"
        "  ttodo tag create -n 'design' -c '#0000ff'"
    ),
)
def create_tag(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="The label text for this tag  (e.g. 'bug', 'feature', 'urgent')",
    ),
    color: str | None = typer.Option(
        None,
        "--color",
        "-c",
        help="A hex color code for this tag  (e.g. #ff0000 for red). Optional.",
    ),
) -> None:
    body: dict = {"name": name}
    if color:
        body["color"] = color
    data = api_call("POST", "/tags", json=body)
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Tag created (ID: {data['id']})")


@app.command(
    "get",
    help="Show details of a specific tag.",
    epilog="Example:  ttodo tag get 2",
)
def get_tag(
    tag_id: int = typer.Argument(
        ...,
        help="The ID number of the tag. Run 'ttodo tag list' to see all IDs.",
    ),
) -> None:
    data = api_call("GET", f"/tags/{tag_id}")
    if state.json_output:
        print_json(data)
    else:
        print_record(
            f"Tag #{tag_id}",
            {"ID": data["id"], "Name": data["name"], "Color": data["color"]},
        )


@app.command(
    "update",
    help=(
        "Change the name or color of an existing tag.\n\n"
        "You only need to provide the fields you want to change."
    ),
    epilog=(
        "Examples:\n\n"
        "  ttodo tag update 2 --name 'critical'\n\n"
        "  ttodo tag update 2 --color '#ff4444'\n\n"
        "  ttodo tag update 2 --name 'critical' --color '#ff4444'"
    ),
)
def update_tag(
    tag_id: int = typer.Argument(
        ...,
        help="The ID number of the tag to update.",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="New label text for this tag.",
    ),
    color: str | None = typer.Option(
        None,
        "--color",
        "-c",
        help="New hex color code  (e.g. #0000ff for blue).",
    ),
) -> None:
    body = {k: v for k, v in {"name": name, "color": color}.items() if v is not None}
    if not body:
        typer.echo(
            "Please specify at least one field to update: --name or --color", err=True
        )
        raise typer.Exit(1)
    data = api_call("PUT", f"/tags/{tag_id}", json=body)
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Tag updated (ID: {data['id']})")


@app.command(
    "delete",
    help=(
        "Delete a tag permanently.\n\n"
        "Deleting a tag will remove it from all todos it was attached to. "
        "Use --yes to skip the confirmation prompt."
    ),
    epilog=("Examples:\n\n  ttodo tag delete 2\n\n  ttodo tag delete 2 --yes"),
)
def delete_tag(
    tag_id: int = typer.Argument(
        ...,
        help="The ID number of the tag to delete.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip the confirmation prompt and delete immediately.",
    ),
) -> None:
    if not yes:
        typer.confirm(f"Delete tag #{tag_id}? This cannot be undone.", abort=True)
    data = api_call("DELETE", f"/tags/{tag_id}")
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Tag #{tag_id} deleted.")
