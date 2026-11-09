"""Domain models for ingested conference data."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Session(BaseModel):
    """A single scheduled session/talk/event."""

    id: str
    title: str
    description: str = ""
    speakers: list[str] = Field(default_factory=list)
    room: str = ""
    track: str = ""  # primary tag, e.g. "Project Lightning Talks"
    flags: list[str] = Field(default_factory=list)  # e.g. "Separate Registration Required"
    start_time: datetime | None = None
    end_time: datetime | None = None
    day: str = ""  # e.g. "2026-11-09"
    url: str = ""

    def to_es_doc(self) -> dict:
        doc = self.model_dump(mode="json")
        return doc


class InfoDoc(BaseModel):
    """A free-form knowledge document (venue, pavilion, FAQ, logistics…)."""

    id: str
    title: str
    body: str
    category: str = "general"  # e.g. "pavilion", "venue", "faq"
    source_url: str = ""

    def to_es_doc(self) -> dict:
        return self.model_dump(mode="json")
