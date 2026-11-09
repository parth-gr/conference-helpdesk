"""Crawler CLI (System 1): scrape conference sources and index them.

Usage:
    python -m conference_helpdesk.crawler ingest [--force-fetch] [--recreate]
    python -m conference_helpdesk.crawler search "query" [--kind sessions|info]
    python -m conference_helpdesk.crawler stats
"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ..config import settings
from . import indexer
from .pipeline import run_ingestion

app = typer.Typer(help="Conference crawler / ingestion CLI", no_args_is_help=True)
console = Console()


@app.command()
def ingest(
    force_fetch: bool = typer.Option(False, help="Bypass the local HTML cache."),
    recreate: bool = typer.Option(False, help="Drop and recreate indices first."),
) -> None:
    """Scrape the conference sources and index them into Elasticsearch."""
    with console.status("Ingesting conference data..."):
        result = run_ingestion(force_fetch=force_fetch, recreate=recreate)
    console.print(
        f"[green]Sessions[/]: scraped {result.sessions_scraped}, "
        f"indexed {result.sessions_indexed}"
    )
    console.print(
        f"[green]Info docs[/]: scraped {result.info_scraped}, "
        f"indexed {result.info_indexed}"
    )


@app.command()
def search(
    query: str,
    kind: str = typer.Option("sessions", help="sessions | info"),
    size: int = typer.Option(5, help="Number of results."),
) -> None:
    """Full-text search the indexed data (quick sanity check)."""
    client = indexer.get_client()
    if kind == "sessions":
        index = settings.es_sessions_index
        fields = ["title^2", "description", "speakers", "track", "room"]
    else:
        index = settings.es_info_index
        fields = ["title^2", "body"]

    resp = client.search(
        index=index,
        query={"multi_match": {"query": query, "fields": fields}},
        size=size,
    )

    table = Table(title=f"Results for '{query}' in {index}")
    table.add_column("Score", justify="right")
    table.add_column("Title")
    table.add_column("Detail", overflow="fold")
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        if kind == "sessions":
            detail = f"{src.get('day','')} {src.get('room','')} — {', '.join(src.get('speakers', []))}"
        else:
            detail = src.get("body", "")[:120]
        table.add_row(f"{hit['_score']:.1f}", src.get("title", ""), detail)
    console.print(table)


@app.command()
def stats() -> None:
    """Show document counts per index."""
    client = indexer.get_client()
    for index in (settings.es_sessions_index, settings.es_info_index):
        if client.indices.exists(index=index):
            count = client.count(index=index)["count"]
            console.print(f"{index}: [cyan]{count}[/] docs")
        else:
            console.print(f"{index}: [red]missing[/]")


if __name__ == "__main__":
    app()
