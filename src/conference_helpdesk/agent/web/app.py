"""FastAPI web app for the Conference Talk Recommender.

Serves a short guided form (a few questions) and returns ranked talk
recommendations straight from Elasticsearch -- no LLM, no chat.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ...recommend import (
    RecommendRequest,
    available_days,
    available_tracks,
    recommend,
)

_STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Conference Talk Recommender")


class RecommendBody(BaseModel):
    interests: list[str] = []
    free_text: str = ""
    level: str = "intermediate"
    day: str = ""
    size: int = 8


@app.get("/api/options")
def options() -> dict:
    """Values to populate the form (tracks and days actually in the index)."""
    return {"tracks": available_tracks(), "days": available_days()}


@app.post("/api/recommend")
def recommend_endpoint(body: RecommendBody) -> dict:
    req = RecommendRequest(
        interests=body.interests,
        free_text=body.free_text,
        level=body.level,
        day=body.day,
        size=body.size,
    )
    recs = recommend(req)
    return {"count": len(recs), "recommendations": [r.to_dict() for r in recs]}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


app.mount("/static", StaticFiles(directory=_STATIC), name="static")
