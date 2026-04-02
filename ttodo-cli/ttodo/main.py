import typer

from ttodo.commands import comments, settings, tags, todos, users
from ttodo.state import state

app = typer.Typer(
    name="ttodo",
    help=(
        "ttodo — Team Todo CLI\n\n"
        "Manage your team's todo list from the terminal.\n\n"
        "Pick a group of commands to get started:\n\n"
        "  ttodo user    — Add or manage team members\n\n"
        "  ttodo todo    — Create and track todo items\n\n"
        "  ttodo comment — Post comments on a todo\n\n"
        "  ttodo tag     — Create labels to organize todos\n\n"
        "  ttodo config  — Set up the server connection\n\n"
        "Run any command with --help for detailed usage.\n\n"
        "Example:\n\n"
        "  ttodo todo list --status in_progress"
    ),
    no_args_is_help=True,
)

app.add_typer(users.app, name="user")
app.add_typer(todos.app, name="todo")
app.add_typer(comments.app, name="comment")
app.add_typer(tags.app, name="tag")
app.add_typer(settings.app, name="config")


@app.callback()
def main(
    json: bool = typer.Option(
        False,
        "--json",
        help="Print the result as JSON instead of a formatted table. Useful for scripting.",
    ),
) -> None:
    state.json_output = json
