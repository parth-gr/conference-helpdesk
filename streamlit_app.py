"""Streamlit UI for the Conference Talk Recommender.

Deployable on Streamlit Community Cloud for a free, always-on public URL.
Reuses the shared ``recommend()`` engine; provide ES_URL / ES_API_KEY via
Streamlit secrets (or a local .env when running locally).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# The package lives under src/ (src layout); make it importable.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

# Bridge Streamlit secrets -> environment BEFORE importing the package, because
# config reads the environment at import time. Locally (no secrets file) this is
# skipped and pydantic-settings falls back to .env.
try:
    for _key in ("ES_URL", "ES_API_KEY", "ES_SESSIONS_INDEX", "ES_INFO_INDEX"):
        if _key not in os.environ and _key in st.secrets:
            os.environ[_key] = str(st.secrets[_key])
except Exception:  # no secrets.toml configured -> rely on .env / real env
    pass

from conference_helpdesk.recommend import (  # noqa: E402
    RecommendRequest,
    available_days,
    available_tracks,
    recommend,
)

st.set_page_config(page_title="Conference Talk Recommender", page_icon="🎟️")

st.title("🎟️ Conference Talk Recommender")
st.caption("Answer a few quick questions and get talk suggestions — no chat, no waiting.")


@st.cache_data(ttl=300)
def _options() -> tuple[list[str], list[str]]:
    return available_tracks(), available_days()


try:
    tracks, days = _options()
except Exception as exc:
    st.error(f"Could not reach Elasticsearch: {exc}")
    st.stop()

if not tracks:
    st.warning(
        "No indexed sessions found. Check ES_URL / ES_API_KEY, or run the crawler "
        "to ingest data first."
    )
    st.stop()

interests = st.multiselect("1. What topics interest you?", tracks)
free_text = st.text_input(
    "Anything else? (free-text keywords)", placeholder="e.g. eBPF, service mesh, gitops"
)
level = st.radio(
    "2. What's your experience level?",
    ["beginner", "intermediate", "advanced"],
    index=1,
    horizontal=True,
)
day = st.selectbox("3. Any particular day?", ["any", *days])

if st.button("Recommend talks →", type="primary"):
    recs = recommend(
        RecommendRequest(
            interests=interests, free_text=free_text, level=level, day=day, size=8
        )
    )
    if not recs:
        st.warning("No matching talks. Try different interests or another day.")
    else:
        st.subheader(f"Top {len(recs)} talks for you")
        for r in recs:
            with st.container(border=True):
                st.markdown(f"**[{r.title}]({r.url})**" if r.url else f"**{r.title}**")
                if r.speakers:
                    st.caption("👤 " + ", ".join(r.speakers))
                when = (r.start_time or r.day or "").replace("T", " ")[:16]
                meta = " · ".join(x for x in (r.track, r.room, when) if x)
                if meta:
                    st.caption(meta)
                st.markdown(f"_{r.reason}_")
