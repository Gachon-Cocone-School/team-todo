import typer

from ttodo.client import api_call
from ttodo.output import print_json, print_record, print_table
from ttodo.state import state

app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Post and manage comments on todo items.\n\n"
        "Comments let team members leave notes, updates, or questions on a specific todo.\n"
        "Each comment is linked to one todo and written by one team member.\n\n"
        "Examples:\n\n"
        "  ttodo comment list 5\n\n"
        "  ttodo comment create 5 --author 1 --content 'Started working on this'\n\n"
        "  ttodo comment delete 3 --yes"
    ),
)


@app.command(
    "list",
    help="Show all comments on a specific todo.",
    epilog="Example:  ttodo comment list 5",
)
def list_comments(
    todo_id: int = typer.Argument(
        ...,
        help="The ID number of the todo whose comments you want to see.",
    ),
) -> None:
    data = api_call("GET", f"/todos/{todo_id}/comments")
    if state.json_output:
        print_json(data)
    else:
        print_table(
            f"Comments on Todo #{todo_id}",
            ["ID", "Author", "Content", "Posted"],
            [
                [c["id"], c["author_id"], c["content"], c["created_at"][:10]]
                for c in data
            ],
        )


@app.command(
    "create",
    help=("Post a new comment on a todo.\n\nBoth --author and --content are required."),
    epilog=(
        "Examples:\n\n"
        "  ttodo comment create 5 --author 1 --content 'Started working on this'\n\n"
        "  ttodo comment create 5 -a 2 -c 'Blocked — need more info'"
    ),
)
def create_comment(
    todo_id: int = typer.Argument(
        ...,
        help="The ID number of the todo to comment on.",
    ),
    author: int = typer.Option(
        ...,
        "--author",
        "-a",
        help="Your user ID — the person writing this comment. Run 'ttodo user list' to find your ID.",
    ),
    content: str = typer.Option(
        ...,
        "--content",
        "-c",
        help="The text of your comment.",
    ),
) -> None:
    data = api_call(
        "POST",
        f"/todos/{todo_id}/comments",
        json={"author_id": author, "content": content},
    )
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Comment posted (ID: {data['id']})")


@app.command(
    "get",
    help="Show the full details of a single comment.",
    epilog="Example:  ttodo comment get 3",
)
def get_comment(
    comment_id: int = typer.Argument(
        ...,
        help="The ID number of the comment. Run 'ttodo comment list <todo_id>' to see all IDs.",
    ),
) -> None:
    data = api_call("GET", f"/comments/{comment_id}")
    if state.json_output:
        print_json(data)
    else:
        print_record(
            f"Comment #{comment_id}",
            {
                "ID": data["id"],
                "Todo": data["todo_id"],
                "Author": data["author_id"],
                "Content": data["content"],
                "Posted": data["created_at"][:10],
            },
        )


@app.command(
    "update",
    help="Edit the text of an existing comment.",
    epilog=(
        "Examples:\n\n"
        "  ttodo comment update 3 --content 'Updated note'\n\n"
        "  ttodo comment update 3 -c 'Fixed typo'"
    ),
)
def update_comment(
    comment_id: int = typer.Argument(
        ...,
        help="The ID number of the comment to edit.",
    ),
    content: str = typer.Option(
        ...,
        "--content",
        "-c",
        help="The new text to replace the existing comment.",
    ),
) -> None:
    data = api_call("PUT", f"/comments/{comment_id}", json={"content": content})
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Comment updated (ID: {data['id']})")


@app.command(
    "delete",
    help=(
        "Delete a comment permanently.\n\n"
        "You will be asked to confirm before deletion. "
        "Use --yes to skip the confirmation prompt."
    ),
    epilog=("Examples:\n\n  ttodo comment delete 3\n\n  ttodo comment delete 3 --yes"),
)
def delete_comment(
    comment_id: int = typer.Argument(
        ...,
        help="The ID number of the comment to delete.",
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
            f"Delete comment #{comment_id}? This cannot be undone.", abort=True
        )
    data = api_call("DELETE", f"/comments/{comment_id}")
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Comment #{comment_id} deleted.")
