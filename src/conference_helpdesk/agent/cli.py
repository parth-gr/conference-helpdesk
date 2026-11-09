"""Agent CLI (System 2): the conference talk recommender.

Usage:
    python -m conference_helpdesk.agent recommend          # interactive
    python -m conference_helpdesk.agent recommend -i Observability -l beginner
    python -m conference_helpdesk.agent serve [--host H] [--port P]  # web form
"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ..recommend import (
    RecommendRequest,
    available_days,
    available_tracks,
    recommend as run_recommend,
)

app = typer.Typer(help="Conference talk recommender CLI", no_args_is_help=True)
console = Console()

_LEVELS = ["beginner", "intermediate", "advanced"]


@app.callback()
def main() -> None:
    """Conference talk recommender (System 2)."""


def _fmt_when(rec) -> str:
    # start_time already carries the date, so prefer it over the bare day.
    if rec.start_time:
        return rec.start_time.replace("T", " ")[:16]
    return rec.day or ""


@app.command()
def recommend(
    interest: list[str] = typer.Option(
        None, "--interest", "-i", help="Topic/track of interest (repeatable)."
    ),
    free_text: str = typer.Option("", "--text", "-t", help="Extra keywords."),
    level: str = typer.Option("", "--level", "-l", help="beginner|intermediate|advanced"),
    day: str = typer.Option("", "--day", "-d", help="Conference day (YYYY-MM-DD) or 'any'."),
    size: int = typer.Option(8, "--size", "-n", help="How many talks to suggest."),
) -> None:
    """Answer a few questions and get recommended talks."""
    interests = list(interest or [])
    tracks = available_tracks()

    # Interactive fill-in when flags are omitted.
    if not interests and not free_text:
        if tracks:
            console.print("[bold]Available topics:[/]")
            for i, t in enumerate(tracks, 1):
                console.print(f"  [cyan]{i}[/]. {t}")
            picked = Prompt.ask(
                "Pick topic numbers (comma-separated, or leave blank)", default=""
            )
            for tok in picked.split(","):
                tok = tok.strip()
                if tok.isdigit() and 1 <= int(tok) <= len(tracks):
                    interests.append(tracks[int(tok) - 1])
        free_text = Prompt.ask("Any other keywords?", default="")

    if not level:
        level = Prompt.ask("Experience level", choices=_LEVELS, default="intermediate")
    if not day:
        days = available_days()
        if days:
            console.print(f"Days: {', '.join(days)}")
        day = Prompt.ask("Which day? (or 'any')", default="any")

    recs = run_recommend(
        RecommendRequest(
            interests=interests, free_text=free_text, level=level, day=day, size=size
        )
    )

    if not recs:
        console.print(
            "[yellow]No matching talks.[/] Try different interests, or run "
            "[bold]crawler ingest[/] if the index is empty."
        )
        raise typer.Exit()

    console.print(f"\n[bold green]Top {len(recs)} talks for you:[/]\n")
    for rec in recs:
        speakers = ", ".join(rec.speakers) if rec.speakers else "—"
        meta = " · ".join(p for p in (rec.track, rec.room, _fmt_when(rec)) if p)
        body = (
            f"[white]{speakers}[/]\n"
            f"[dim]{meta}[/]\n"
            f"[cyan italic]{rec.reason}[/]"
        )
        if rec.url:
            body += f"\n[dim]{rec.url}[/]"
        console.print(Panel(body, title=rec.title, title_align="left", border_style="blue"))


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host."),
    port: int = typer.Option(8000, help="Bind port."),
) -> None:
    """Run the web form (browser-based talk recommender)."""
    import uvicorn

    console.print(
        f"[bold cyan]Conference Talk Recommender[/] on http://{host}:{port}"
    )
    uvicorn.run("conference_helpdesk.agent.web.app:app", host=host, port=port)


if __name__ == "__main__":
    app()
