"""Orchestrate the full ingestion: fetch -> scrape -> index."""
from __future__ import annotations

from dataclasses import dataclass

from ..config import settings
from . import indexer
from .fetch import fetch_html
from .pavilion_scraper import parse_pavilion
from .schedule_scraper import parse_schedule


@dataclass
class IngestResult:
    sessions_scraped: int
    sessions_indexed: int
    info_scraped: int
    info_indexed: int


def run_ingestion(*, force_fetch: bool = False, recreate: bool = False) -> IngestResult:
    """Scrape both sources and index everything into Elasticsearch."""
    schedule_html = fetch_html(settings.schedule_url, force=force_fetch)
    sessions = parse_schedule(schedule_html)

    pavilion_html = fetch_html(settings.pavilion_url, force=force_fetch)
    info = parse_pavilion(pavilion_html, source_url=settings.pavilion_url)

    client = indexer.get_client()
    indexer.ensure_index(
        client, settings.es_sessions_index, indexer.SESSIONS_MAPPING, recreate=recreate
    )
    indexer.ensure_index(
        client, settings.es_info_index, indexer.INFO_MAPPING, recreate=recreate
    )

    sessions_indexed = indexer.index_sessions(client, sessions)
    info_indexed = indexer.index_info(client, info)
    client.indices.refresh(index=[settings.es_sessions_index, settings.es_info_index])

    return IngestResult(
        sessions_scraped=len(sessions),
        sessions_indexed=sessions_indexed,
        info_scraped=len(info),
        info_indexed=info_indexed,
    )
