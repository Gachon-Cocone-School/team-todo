import json as json_lib

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def print_json(data: dict | list) -> None:
    typer.echo(json_lib.dumps(data, ensure_ascii=False, indent=2))


def print_table(title: str, columns: list[str], rows: list[list]) -> None:
    if not rows:
        typer.echo("결과 없음")
        return
    table = Table(title=title or None, show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(v) if v is not None else "-" for v in row])
    console.print(table)


def print_record(title: str, data: dict) -> None:
    table = Table(title=title or None, show_header=False)
    table.add_column("필드", style="bold")
    table.add_column("값")
    for key, value in data.items():
        table.add_row(key, str(value) if value is not None else "-")
    console.print(table)
