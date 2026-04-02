import typer

from ttodo.client import api_call
from ttodo.output import print_json, print_record, print_table
from ttodo.state import state

app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Manage team members.\n\n"
        "Team members can be assigned to todos and leave comments.\n"
        "Each member has a unique ID that you'll use in other commands.\n\n"
        "Examples:\n\n"
        "  ttodo user list\n\n"
        "  ttodo user create --name 'Jane Smith' --email jane@company.com\n\n"
        "  ttodo user get 3"
    ),
)


@app.command(
    "list",
    help="Show all team members.",
    epilog="Example:  ttodo user list",
)
def list_users() -> None:
    data = api_call("GET", "/users")
    if state.json_output:
        print_json(data)
    else:
        print_table(
            "Team Members",
            ["ID", "Name", "Email", "Joined"],
            [[u["id"], u["name"], u["email"], u["created_at"][:10]] for u in data],
        )


@app.command(
    "create",
    help="Add a new team member.",
    epilog="Example:  ttodo user create --name 'Jane Smith' --email jane@company.com",
)
def create_user(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Full name of the team member  (e.g. Jane Smith)",
    ),
    email: str = typer.Option(
        ...,
        "--email",
        "-e",
        help="Email address. Must be unique across all team members.",
    ),
) -> None:
    data = api_call("POST", "/users", json={"name": name, "email": email})
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Team member created (ID: {data['id']})")
        print_record(
            "", {"ID": data["id"], "Name": data["name"], "Email": data["email"]}
        )


@app.command(
    "get",
    help="Show details of a specific team member.",
    epilog="Example:  ttodo user get 3",
)
def get_user(
    user_id: int = typer.Argument(
        ...,
        help="The ID number of the team member. Run 'ttodo user list' to see all IDs.",
    ),
) -> None:
    data = api_call("GET", f"/users/{user_id}")
    if state.json_output:
        print_json(data)
    else:
        print_record(
            f"Team Member #{user_id}",
            {
                "ID": data["id"],
                "Name": data["name"],
                "Email": data["email"],
                "Joined": data["created_at"][:10],
            },
        )


@app.command(
    "update",
    help=(
        "Change a team member's name or email address.\n\n"
        "You only need to provide the fields you want to change."
    ),
    epilog=(
        "Examples:\n\n"
        "  ttodo user update 3 --name 'Jane Lee'\n\n"
        "  ttodo user update 3 --email new@company.com\n\n"
        "  ttodo user update 3 --name 'Jane Lee' --email new@company.com"
    ),
)
def update_user(
    user_id: int = typer.Argument(
        ...,
        help="The ID number of the team member to update.",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="New name for the team member.",
    ),
    email: str | None = typer.Option(
        None,
        "--email",
        "-e",
        help="New email address for the team member.",
    ),
) -> None:
    body = {k: v for k, v in {"name": name, "email": email}.items() if v is not None}
    if not body:
        typer.echo(
            "Please specify at least one field to update: --name or --email", err=True
        )
        raise typer.Exit(1)
    data = api_call("PUT", f"/users/{user_id}", json=body)
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Team member updated (ID: {data['id']})")


@app.command(
    "delete",
    help=(
        "Remove a team member permanently.\n\n"
        "You will be asked to confirm before deletion. "
        "Use --yes to skip the confirmation prompt."
    ),
    epilog=("Examples:\n\n  ttodo user delete 3\n\n  ttodo user delete 3 --yes"),
)
def delete_user(
    user_id: int = typer.Argument(
        ...,
        help="The ID number of the team member to delete.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip the confirmation prompt and delete immediately.",
    ),
) -> None:
    if not yes:
        typer.confirm(
            f"Delete team member #{user_id}? This cannot be undone.", abort=True
        )
    data = api_call("DELETE", f"/users/{user_id}")
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Team member #{user_id} deleted.")
