"""Central configuration, loaded from environment / .env."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    es_url: str = "http://localhost:9200"
    es_api_key: str = ""
    es_sessions_index: str = "conference_sessions"
    es_info_index: str = "conference_info"

    # Helpdesk agent (System 2) -- Elastic Agent Builder
    # The web helpdesk talks to Elastic's Agent Builder "Converse" API, so the
    # LLM is managed by Elastic (no provider key needed). Reuses ES_API_KEY.
    kibana_url: str = ""
    agent_id: str = "elastic-ai-agent"

    schedule_url: str = (
        "https://events.linuxfoundation.org/"
        "kubecon-cloudnativecon-north-america/program/schedule/"
    )
    pavilion_url: str = (
        "https://events.linuxfoundation.org/"
        "kubecon-cloudnativecon-north-america/features-add-ons/project-engagement/"
    )

    cache_dir: str = ".cache"


settings = Settings()
