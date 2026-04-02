from enum import Enum

import typer

from ttodo.client import api_call
from ttodo.output import print_json, print_record, print_table
from ttodo.state import state

app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Create and manage todo items.\n\n"
        "Each todo can have a priority, due date, assignee, and tags.\n"
        "Use filters on 'list' to find the todos you care about.\n\n"
        "Examples:\n\n"
        "  ttodo todo list\n\n"
        "  ttodo todo list --status in_progress --priority high\n\n"
        "  ttodo todo create --title 'Fix login bug' --created-by 1\n\n"
        "  ttodo todo update 5 --status done"
    ),
)


class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


def _todo_row(t: dict) -> list:
    tags = ", ".join(tag["name"] for tag in t.get("tags", []))
    return [
        t["id"],
        t["title"],
        t["status"],
        t["priority"],
        t["due_date"] or "-",
        t["assignee_id"] or "-",
        tags or "-",
    ]


@app.command(
    "list",
    help=(
        "Show all todos. Use filters to narrow the results.\n\n"
        "Status choices:   todo | in_progress | done\n\n"
        "Priority choices: low | medium | high"
    ),
    epilog=(
        "Examples:\n\n"
        "  ttodo todo list\n\n"
        "  ttodo todo list --status todo\n\n"
        "  ttodo todo list --priority high\n\n"
        "  ttodo todo list --status in_progress --priority high\n\n"
        "  ttodo todo list --assignee 2\n\n"
        "  ttodo todo list --tag 1"
    ),
)
def list_todos(
    status: Status | None = typer.Option(
        None,
        "--status",
        "-s",
        help="Show only todos with this status: todo, in_progress, done",
    ),
    priority: Priority | None = typer.Option(
        None,
        "--priority",
        "-p",
        help="Show only todos with this priority: low, medium, high",
    ),
    assignee: int | None = typer.Option(
        None,
        "--assignee",
        "-a",
        help="Show only todos assigned to this user ID.",
    ),
    tag: int | None = typer.Option(
        None,
        "--tag",
        "-t",
        help="Show only todos that have this tag ID attached.",
    ),
) -> None:
    params: dict = {}
    if status:
        params["status"] = status.value
    if priority:
        params["priority"] = priority.value
    if assignee:
        params["assignee_id"] = assignee
    if tag:
        params["tag_id"] = tag
    data = api_call("GET", "/todos", params=params)
    if state.json_output:
        print_json(data)
    else:
        print_table(
            "Todo List",
            ["ID", "Title", "Status", "Priority", "Due Date", "Assignee", "Tags"],
            [_todo_row(t) for t in data],
        )


@app.command(
    "create",
    help=(
        "Create a new todo item.\n\n"
        "Only --title and --created-by are required. All other fields are optional.\n\n"
        "Status choices:   todo | in_progress | done  (default: todo)\n\n"
        "Priority choices: low | medium | high  (default: medium)"
    ),
    epilog=(
        "Examples:\n\n"
        "  ttodo todo create --title 'Fix login bug' --created-by 1\n\n"
        "  ttodo todo create --title 'Write docs' --created-by 1 --priority high --due-date 2026-04-30\n\n"
        "  ttodo todo create --title 'Review PR' --created-by 1 --assignee 2 --status in_progress"
    ),
)
def create_todo(
    title: str = typer.Option(
        ...,
        "--title",
        help="Short title describing what needs to be done  (e.g. 'Fix login bug')",
    ),
    created_by: int = typer.Option(
        ...,
        "--created-by",
        help="Your user ID — the person creating this todo. Run 'ttodo user list' to find your ID.",
    ),
    description: str | None = typer.Option(
        None,
        "--description",
        "-d",
        help="Optional longer description with more details about the todo.",
    ),
    status: Status = typer.Option(
        Status.todo,
        "--status",
        "-s",
        help="Initial status of the todo. Default is 'todo'.",
    ),
    priority: Priority = typer.Option(
        Priority.medium,
        "--priority",
        "-p",
        help="How urgent is this todo? Default is 'medium'.",
    ),
    due_date: str | None = typer.Option(
        None,
        "--due-date",
        help="Deadline in YYYY-MM-DD format  (e.g. 2026-04-30)",
    ),
    assignee: int | None = typer.Option(
        None,
        "--assignee",
        "-a",
        help="User ID of the person responsible for completing this todo.",
    ),
) -> None:
    body: dict = {
        "title": title,
        "created_by": created_by,
        "status": status.value,
        "priority": priority.value,
    }
    if description:
        body["description"] = description
    if due_date:
        body["due_date"] = due_date
    if assignee:
        body["assignee_id"] = assignee
    data = api_call("POST", "/todos", json=body)
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Todo created (ID: {data['id']})")


@app.command(
    "get",
    help="Show full details of a single todo, including its tags and description.",
    epilog="Example:  ttodo todo get 5",
)
def get_todo(
    todo_id: int = typer.Argument(
        ...,
        help="The ID number of the todo. Run 'ttodo todo list' to see all IDs.",
    ),
) -> None:
    data = api_call("GET", f"/todos/{todo_id}")
    if state.json_output:
        print_json(data)
    else:
        tags = ", ".join(t["name"] for t in data.get("tags", []))
        print_record(
            f"Todo #{todo_id}",
            {
                "ID": data["id"],
                "Title": data["title"],
                "Description": data["description"],
                "Status": data["status"],
                "Priority": data["priority"],
                "Due Date": data["due_date"],
                "Assignee": data["assignee_id"],
                "Created By": data["created_by"],
                "Tags": tags or "-",
                "Created": data["created_at"][:10],
                "Updated": data["updated_at"][:10],
            },
        )


@app.command(
    "update",
    help=(
        "Change one or more fields of an existing todo.\n\n"
        "Only the fields you provide will be changed — others stay the same.\n\n"
        "Status choices:   todo | in_progress | done\n\n"
        "Priority choices: low | medium | high"
    ),
    epilog=(
        "Examples:\n\n"
        "  ttodo todo update 5 --status done\n\n"
        "  ttodo todo update 5 --priority high --due-date 2026-05-01\n\n"
        "  ttodo todo update 5 --assignee 2 --status in_progress"
    ),
)
def update_todo(
    todo_id: int = typer.Argument(
        ...,
        help="The ID number of the todo to update.",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        help="New title for the todo.",
    ),
    description: str | None = typer.Option(
        None,
        "--description",
        "-d",
        help="New description for the todo.",
    ),
    status: Status | None = typer.Option(
        None,
        "--status",
        "-s",
        help="New status: todo, in_progress, done",
    ),
    priority: Priority | None = typer.Option(
        None,
        "--priority",
        "-p",
        help="New priority: low, medium, high",
    ),
    due_date: str | None = typer.Option(
        None,
        "--due-date",
        help="New deadline in YYYY-MM-DD format  (e.g. 2026-05-01)",
    ),
    assignee: int | None = typer.Option(
        None,
        "--assignee",
        "-a",
        help="User ID of the new person responsible for this todo.",
    ),
) -> None:
    body: dict = {}
    if title is not None:
        body["title"] = title
    if description is not None:
        body["description"] = description
    if status is not None:
        body["status"] = status.value
    if priority is not None:
        body["priority"] = priority.value
    if due_date is not None:
        body["due_date"] = due_date
    if assignee is not None:
        body["assignee_id"] = assignee
    if not body:
        typer.echo("Please specify at least one field to update.", err=True)
        raise typer.Exit(1)
    data = api_call("PUT", f"/todos/{todo_id}", json=body)
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Todo updated (ID: {data['id']})")


@app.command(
    "delete",
    help=(
        "Delete a todo permanently. All comments on that todo will also be deleted.\n\n"
        "You will be asked to confirm before deletion. "
        "Use --yes to skip the confirmation prompt."
    ),
    epilog=("Examples:\n\n  ttodo todo delete 5\n\n  ttodo todo delete 5 --yes"),
)
def delete_todo(
    todo_id: int = typer.Argument(
        ...,
        help="The ID number of the todo to delete.",
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
            f"Delete todo #{todo_id}? All its comments will also be deleted.",
            abort=True,
        )
    data = api_call("DELETE", f"/todos/{todo_id}")
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Todo #{todo_id} deleted.")


@app.command(
    "attach-tag",
    help=(
        "Add a tag to a todo.\n\n"
        "Run 'ttodo tag list' to see available tags and their IDs."
    ),
    epilog="Example:  ttodo todo attach-tag 5 2",
)
def attach_tag(
    todo_id: int = typer.Argument(
        ...,
        help="The ID number of the todo.",
    ),
    tag_id: int = typer.Argument(
        ...,
        help="The ID number of the tag to attach. Run 'ttodo tag list' to see all tags.",
    ),
) -> None:
    data = api_call("POST", f"/todos/{todo_id}/tags/{tag_id}")
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Tag #{tag_id} attached to todo #{todo_id}.")


@app.command(
    "detach-tag",
    help="Remove a tag from a todo. The tag itself will not be deleted.",
    epilog="Example:  ttodo todo detach-tag 5 2",
)
def detach_tag(
    todo_id: int = typer.Argument(
        ...,
        help="The ID number of the todo.",
    ),
    tag_id: int = typer.Argument(
        ...,
        help="The ID number of the tag to remove.",
    ),
) -> None:
    data = api_call("DELETE", f"/todos/{todo_id}/tags/{tag_id}")
    if state.json_output:
        print_json(data)
    else:
        typer.echo(f"Tag #{tag_id} removed from todo #{todo_id}.")
