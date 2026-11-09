"""Agent CLI (System 2): run the web helpdesk backed by Elastic Agent Builder.

Usage:
    python -m conference_helpdesk.agent serve [--host H] [--port P]
"""
from __future__ import annotations

import typer
from rich.console import Console

from ..config import settings

app = typer.Typer(help="Conference helpdesk agent CLI", no_args_is_help=True)
console = Console()


@app.callback()
def main() -> None:
    """Conference helpdesk agent (System 2), backed by Elastic Agent Builder."""


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host."),
    port: int = typer.Option(8000, help="Bind port."),
) -> None:
    """Run the web helpdesk (browser chat backed by Elastic Agent Builder)."""
    import uvicorn

    if not settings.kibana_url:
        console.print("[red]KIBANA_URL is not set in .env[/] — required for the web helpdesk.")
        raise typer.Exit(code=1)
    console.print(
        f"[bold cyan]Conference Helpdesk[/] on http://{host}:{port} "
        f"(agent: {settings.agent_id})"
    )
    uvicorn.run("conference_helpdesk.agent.web.app:app", host=host, port=port)


if __name__ == "__main__":
    app()
