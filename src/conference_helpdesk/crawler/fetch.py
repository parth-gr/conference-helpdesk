"""HTTP fetching with a simple on-disk cache.

The cache keeps development fast and avoids repeatedly hitting the source
site. Pass ``force=True`` to bypass it.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import requests

from ..config import settings

_USER_AGENT = "conference-helpdesk-ingest/0.1 (+https://github.com/)"


def _cache_path(url: str) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    return Path(settings.cache_dir) / f"{key}.html"


def fetch_html(url: str, *, force: bool = False, timeout: int = 60) -> str:
    """Return page HTML, using the on-disk cache unless ``force`` is set."""
    cache = _cache_path(url)
    if cache.exists() and not force:
        return cache.read_text(encoding="utf-8")

    resp = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    html = resp.text

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(html, encoding="utf-8")
    return html
