"""Parse the Project Engagement / Project Pavilion page into InfoDocs.

The page is organised as heading-delimited sections (Project Pavilion,
Kiosk Directory, FAQs, Maintainer Summit, …). Each heading and the content
up to the next heading of the same level becomes one knowledge document.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..models import InfoDoc

_HEADINGS = ("h1", "h2", "h3")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def parse_pavilion(html: str, source_url: str = "") -> list[InfoDoc]:
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main") or soup.select_one("article") or soup.body
    if main is None:
        return []

    # Walk headings and content blocks in document order, assigning each
    # block of text to the most recent preceding heading.
    sections: list[tuple[str, list[str]]] = []
    seen_blocks: set[str] = set()
    for el in main.find_all([*_HEADINGS, "p", "li", "dd", "td"]):
        if el.name in _HEADINGS:
            title = el.get_text(" ", strip=True)
            if title:
                sections.append((title, []))
            continue
        if not sections:
            continue
        text = el.get_text(" ", strip=True)
        # Skip empties and blocks already captured (nested list/table items).
        if not text or text in seen_blocks:
            continue
        seen_blocks.add(text)
        sections[-1][1].append(text)

    docs: list[InfoDoc] = []
    for title, parts in sections:
        body = "\n".join(parts).strip()
        if not body:
            continue
        docs.append(
            InfoDoc(
                id=f"pavilion-{_slugify(title)}",
                title=title,
                body=body,
                category="pavilion",
                source_url=source_url,
            )
        )
    return docs
