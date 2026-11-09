"""Elasticsearch index management and bulk indexing."""
from __future__ import annotations

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from ..config import settings
from ..models import InfoDoc, Session

SESSIONS_MAPPING = {
    "properties": {
        "id": {"type": "keyword"},
        "title": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "description": {"type": "text"},
        "speakers": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "room": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "track": {"type": "keyword"},
        "flags": {"type": "keyword"},
        "start_time": {"type": "date"},
        "end_time": {"type": "date"},
        "day": {"type": "keyword"},
        "url": {"type": "keyword"},
    }
}

INFO_MAPPING = {
    "properties": {
        "id": {"type": "keyword"},
        "title": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "body": {"type": "text"},
        "category": {"type": "keyword"},
        "source_url": {"type": "keyword"},
    }
}


def get_client() -> Elasticsearch:
    if settings.es_api_key:
        return Elasticsearch(settings.es_url, api_key=settings.es_api_key)
    return Elasticsearch(settings.es_url)


def ensure_index(client: Elasticsearch, name: str, mapping: dict, *, recreate: bool = False) -> None:
    if recreate and client.indices.exists(index=name):
        client.indices.delete(index=name)
    if not client.indices.exists(index=name):
        client.indices.create(index=name, mappings=mapping)


def index_sessions(client: Elasticsearch, sessions: list[Session]) -> int:
    actions = (
        {
            "_index": settings.es_sessions_index,
            "_id": s.id,
            "_source": s.to_es_doc(),
        }
        for s in sessions
    )
    ok, _ = bulk(client, actions)
    return ok


def index_info(client: Elasticsearch, docs: list[InfoDoc]) -> int:
    actions = (
        {
            "_index": settings.es_info_index,
            "_id": d.id,
            "_source": d.to_es_doc(),
        }
        for d in docs
    )
    ok, _ = bulk(client, actions)
    return ok
