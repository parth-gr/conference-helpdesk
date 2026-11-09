"""Parse the KubeCon (Sched.com SSR) schedule page into Session models.

The schedule page server-renders every session. Each session lives in a
``div.sess-wrap`` with a visible card plus a hidden ``div.sess__seo`` block
that carries machine-readable start/end times and the full description.
"""
from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from ..models import Session


def _text(node) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_one(wrap) -> Session | None:
    link = wrap.select_one("a.sess-link")
    if link is None:
        return None

    session_id = link.get("data-session-id") or ""
    if not session_id:
        return None

    title = _text(wrap.select_one(".sess__title"))

    speakers_raw = _text(wrap.select_one(".sess__speakers"))
    speakers = [s.strip() for s in speakers_raw.split(",") if s.strip()]

    tags = [_text(t) for t in wrap.select(".sess__tags .tag")]
    track = tags[0] if tags else ""
    flags = tags[1:]

    times = wrap.select(".sess__seotime time")
    start = _parse_dt(times[0].get("datetime")) if len(times) >= 1 else None
    end = _parse_dt(times[1].get("datetime")) if len(times) >= 2 else None

    return Session(
        id=session_id,
        title=title,
        description=_text(wrap.select_one(".sess__seodesc")),
        speakers=speakers,
        room=_text(wrap.select_one(".sess__room")),
        track=track,
        flags=flags,
        start_time=start,
        end_time=end,
        day=start.date().isoformat() if start else "",
        url=link.get("href", ""),
    )


def parse_schedule(html: str) -> list[Session]:
    """Return all sessions found on the schedule page, de-duplicated by id."""
    soup = BeautifulSoup(html, "lxml")
    sessions: dict[str, Session] = {}
    for wrap in soup.select("div.sess-wrap"):
        session = _parse_one(wrap)
        if session is not None:
            sessions[session.id] = session
    return list(sessions.values())
