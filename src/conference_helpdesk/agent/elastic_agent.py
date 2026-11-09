"""Client for Elastic Agent Builder's "Converse" API (System 2, web backend).

Instead of calling an LLM provider directly, the helpdesk talks to an Elastic
Agent Builder agent running on the Kibana side of the Elastic cluster. Elastic
manages the LLM (via its connector), and the agent already has tools to search
the indexed conference data -- so no Anthropic/OpenAI key is required, just the
same Elasticsearch API key used for ingestion.
"""
from __future__ import annotations

import requests

from ..config import settings


class ElasticAgentError(RuntimeError):
    """Raised when the Agent Builder Converse API returns an error."""


class ConverseClient:
    """Thin wrapper over POST /api/agent_builder/converse.

    Stateless across instances; multi-turn context is maintained by passing the
    ``conversation_id`` returned from the previous round back into the next call.
    """

    def __init__(
        self,
        *,
        kibana_url: str | None = None,
        api_key: str | None = None,
        agent_id: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.kibana_url = (kibana_url or settings.kibana_url).rstrip("/")
        self.api_key = api_key or settings.es_api_key
        self.agent_id = agent_id or settings.agent_id
        self.timeout = timeout
        if not self.kibana_url:
            raise ElasticAgentError(
                "KIBANA_URL is not configured (needed for Agent Builder)."
            )
        if not self.api_key:
            raise ElasticAgentError("ES_API_KEY is not configured.")

    def converse(self, message: str, conversation_id: str | None = None) -> dict:
        """Send one user message; return {'reply': str, 'conversation_id': str}."""
        body: dict = {"agent_id": self.agent_id, "input": message}
        if conversation_id:
            body["conversation_id"] = conversation_id

        resp = requests.post(
            f"{self.kibana_url}/api/agent_builder/converse",
            headers={
                "Authorization": f"ApiKey {self.api_key}",
                "kbn-xsrf": "true",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise ElasticAgentError(
                f"Converse API returned {resp.status_code}: {resp.text[:500]}"
            )
        data = resp.json()
        return {
            "reply": (data.get("response") or {}).get("message", ""),
            "conversation_id": data.get("conversation_id"),
        }
