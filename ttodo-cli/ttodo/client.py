from typing import Any

import httpx
import typer

from ttodo.config import get_server_url


def _handle_response(response: httpx.Response) -> Any:
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        typer.echo(f"오류 {response.status_code}: {detail}", err=True)
        raise typer.Exit(1)
    return response.json()


def api_call(method: str, path: str, **kwargs: Any) -> Any:
    server_url = get_server_url()
    try:
        with httpx.Client(base_url=server_url, timeout=10.0) as client:
            response = client.request(method, path, **kwargs)
            return _handle_response(response)
    except httpx.ConnectError:
        typer.echo(f"서버 연결 실패: {server_url}", err=True)
        typer.echo("서버 주소 확인: ttodo config show", err=True)
        raise typer.Exit(1)
    except httpx.TimeoutException:
        typer.echo(f"서버 응답 시간 초과: {server_url}", err=True)
        raise typer.Exit(1)
