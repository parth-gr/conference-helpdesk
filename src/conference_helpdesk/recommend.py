"""Talk recommendation logic (shared by the web form and the CLI).

Given a few answers (interests, experience level, optional day) this builds an
Elasticsearch query against the sessions index and returns ranked talks. It is
pure Elasticsearch -- no LLM -- so it is fast, deterministic, and unaffected by
the Agent Builder trial quota.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import settings
from .crawler.indexer import get_client

# Experience level -> words that tend to appear in talks at that level. Used as a
# soft boost, never a hard filter (so you still get results if nothing matches).
LEVEL_HINTS: dict[str, list[str]] = {
    "beginner": ["intro", "introduction", "getting started", "beginner", "101", "basics"],
    "intermediate": [],
    "advanced": ["deep dive", "advanced", "internals", "at scale", "production", "under the hood"],
}


@dataclass
class Recommendation:
    id: str
    title: str
    speakers: list[str]
    room: str
    track: str
    day: str
    start_time: str | None
    end_time: str | None
    url: str
    score: float
    reason: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "speakers": self.speakers,
            "room": self.room,
            "track": self.track,
            "day": self.day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "url": self.url,
            "score": round(self.score, 2),
            "reason": self.reason,
        }


@dataclass
class RecommendRequest:
    interests: list[str] = field(default_factory=list)  # selected tracks / tags
    free_text: str = ""  # anything extra the user typed
    level: str = "intermediate"
    day: str = ""  # "" or "any" => no day filter
    size: int = 8


def _sessions_index_ready(client) -> bool:
    return client.indices.exists(index=settings.es_sessions_index)


def available_tracks(limit: int = 40) -> list[str]:
    """Distinct track values present in the index, most common first."""
    client = get_client()
    if not _sessions_index_ready(client):
        return []
    resp = client.search(
        index=settings.es_sessions_index,
        size=0,
        aggs={"tracks": {"terms": {"field": "track", "size": limit}}},
    )
    buckets = resp["aggregations"]["tracks"]["buckets"]
    return [b["key"] for b in buckets if b["key"]]


def available_days(limit: int = 20) -> list[str]:
    """Distinct conference days present in the index, earliest first."""
    client = get_client()
    if not _sessions_index_ready(client):
        return []
    resp = client.search(
        index=settings.es_sessions_index,
        size=0,
        aggs={"days": {"terms": {"field": "day", "size": limit, "order": {"_key": "asc"}}}},
    )
    buckets = resp["aggregations"]["days"]["buckets"]
    return [b["key"] for b in buckets if b["key"]]


def _build_reason(src: dict, interests: list[str], level: str) -> str:
    bits: list[str] = []
    track = src.get("track", "")
    if track and track in interests:
        bits.append(f"is in the {track} track you picked")
    elif interests:
        hay = f"{src.get('title','')} {src.get('description','')}".lower()
        matched = [i for i in interests if i.lower() in hay]
        if matched:
            bits.append("matches " + ", ".join(matched))
    level_terms = LEVEL_HINTS.get(level.lower(), [])
    hay = f"{src.get('title','')} {src.get('description','')}".lower()
    if any(t in hay for t in level_terms):
        bits.append(f"looks {level.lower()}-friendly")
    if not bits:
        if track:
            bits.append(f"is a {track} session")
        else:
            bits.append("is a relevant session")
    return "Suggested because it " + " and ".join(bits) + "."


def recommend(req: RecommendRequest) -> list[Recommendation]:
    """Return ranked talk recommendations for the given answers."""
    client = get_client()
    if not _sessions_index_ready(client):
        return []

    should: list[dict] = []
    text_terms = [*req.interests]
    if req.free_text.strip():
        text_terms.append(req.free_text.strip())
    text = " ".join(text_terms).strip()

    if text:
        should.append(
            {
                "multi_match": {
                    "query": text,
                    "fields": ["title^3", "description", "track^2", "speakers", "room"],
                    "type": "best_fields",
                }
            }
        )
    if req.interests:
        should.append({"terms": {"track": req.interests, "boost": 2}})

    level_terms = LEVEL_HINTS.get(req.level.lower(), [])
    if level_terms:
        should.append(
            {"multi_match": {"query": " ".join(level_terms), "fields": ["title^2", "description"]}}
        )

    filters: list[dict] = []
    if req.day and req.day.lower() != "any":
        filters.append({"term": {"day": req.day}})

    if should:
        query: dict = {"bool": {"should": should, "minimum_should_match": 1}}
        if filters:
            query["bool"]["filter"] = filters
    elif filters:
        query = {"bool": {"filter": filters}}
    else:
        query = {"match_all": {}}

    resp = client.search(index=settings.es_sessions_index, query=query, size=req.size)

    results: list[Recommendation] = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        results.append(
            Recommendation(
                id=src.get("id", hit["_id"]),
                title=src.get("title", ""),
                speakers=src.get("speakers", []),
                room=src.get("room", ""),
                track=src.get("track", ""),
                day=src.get("day", ""),
                start_time=src.get("start_time"),
                end_time=src.get("end_time"),
                url=src.get("url", ""),
                score=hit.get("_score") or 0.0,
                reason=_build_reason(src, req.interests, req.level),
            )
        )
    return results
