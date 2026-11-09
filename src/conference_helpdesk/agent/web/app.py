"""FastAPI web app for the Conference Helpdesk (System 2).

Serves a browser chat UI and proxies messages to Elastic Agent Builder's
Converse API. The Elastic API key stays on the server and is never exposed to
the browser.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..elastic_agent import ConverseClient, ElasticAgentError

_STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Conference Helpdesk")


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str | None = None
    error: str | None = None


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        client = ConverseClient()
        result = client.converse(req.message, conversation_id=req.conversation_id)
        return ChatResponse(
            reply=result["reply"], conversation_id=result["conversation_id"]
        )
    except ElasticAgentError as exc:
        return ChatResponse(reply="", error=str(exc))


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


app.mount("/static", StaticFiles(directory=_STATIC), name="static")
