"""AgentOS bridge: the only service that imports the Cognee SDK.

Four endpoints, no business logic — thin pass-throughs to
cognee.remember() / recall() / improve() / forget(). See ARCHITECTURE.md §2.2.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import cognee
from cognee import SearchType
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AgentOS Bridge")

COGNEE_SERVICE_URL = os.getenv("COGNEE_SERVICE_URL")
COGNEE_API_KEY = os.getenv("COGNEE_API_KEY")

DATASET_NAME = "agentos_project"


@app.on_event("startup")
async def connect_cognee_cloud():
    """Switch the SDK into remote mode against Cognee Cloud.

    Without this, remember()/recall()/improve()/forget() run against a
    local SQLite/LanceDB/Ladybug stack instead of the tenant configured
    via COGNEE_SERVICE_URL/COGNEE_API_KEY.
    """
    if COGNEE_SERVICE_URL:
        await cognee.serve(COGNEE_SERVICE_URL, COGNEE_API_KEY)


class RememberRequest(BaseModel):
    content: str
    tags: Optional[dict[str, Any]] = None


class RecallRequest(BaseModel):
    query: str
    filters: Optional[dict[str, Any]] = None
    top_k: int = 15


class ImproveRequest(BaseModel):
    session_id: Optional[str] = None


class ForgetRequest(BaseModel):
    target: str


def _tag_text(content: str, tags: Optional[dict[str, Any]]) -> str:
    """Fold tags into the remembered text so they're recoverable via recall.

    Cognee's remember() takes free text, not structured metadata, so tags
    (agent/type/status/created_at) are embedded as a prefix line.
    """
    tags = dict(tags or {})
    tags.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    tag_line = " ".join(f"{k}={v}" for k, v in tags.items())
    return f"[{tag_line}]\n{content}"


@app.post("/remember")
async def remember(req: RememberRequest):
    text = _tag_text(req.content, req.tags)
    result = await cognee.remember(text, dataset_name=DATASET_NAME)
    # Remote mode (cognee.serve) returns a plain dict from the cloud API;
    # local-SDK mode returns a RememberResult object — handle both.
    return result.to_dict() if hasattr(result, "to_dict") else result


@app.post("/recall")
async def recall(req: RecallRequest):
    query = req.query
    if req.filters:
        query = " ".join(f"{k}={v}" for k, v in req.filters.items()) + " " + query
    results = await cognee.recall(query, datasets=[DATASET_NAME], top_k=req.top_k)
    return {"results": [r.model_dump() if hasattr(r, "model_dump") else r for r in results]}


@app.post("/improve")
async def improve(req: ImproveRequest):
    """Trigger graph enrichment.

    Some Cognee Cloud tenant builds don't expose /api/v1/improve yet — the
    primary improve() lifecycle coverage for this project is the Claude Code
    plugin's automatic SessionEnd hook (see docs/architecture.md), so a
    missing route here is reported, not fatal.
    """
    kwargs: dict[str, Any] = {"dataset": DATASET_NAME}
    if req.session_id:
        kwargs["session_ids"] = [req.session_id]
    try:
        result = await cognee.improve(**kwargs)
    except RuntimeError as exc:
        return {"status": "unavailable", "error": str(exc)}
    return {"status": "completed", "raw": str(result)}


@app.post("/forget")
async def forget(req: ForgetRequest):
    """Find the data item whose stored text mentions `target`, then forget it.

    cognee.forget() only deletes by data_id/dataset/everything — it has no
    text-query form. So we resolve target -> data_id via a CHUNKS recall,
    whose payload carries the source data_id in metadata (works in both
    local and Cognee Cloud remote mode; local-disk reads of raw_data_location
    would not, since that path lives on the cloud tenant, not this machine).
    """
    hits = await cognee.recall(
        req.target,
        query_type=SearchType.CHUNKS,
        datasets=[DATASET_NAME],
        top_k=5,
    )

    # CHUNKS is relevance-ranked, not exact-match — trust the top hit's
    # data_id rather than also requiring a literal substring match, since
    # chunk boundaries can split the sentence the target text refers to.
    for hit in hits:
        # Remote mode (cognee.serve) returns plain dicts from the cloud API;
        # local-SDK mode returns SearchResultItem objects — handle both.
        hit_dict = hit if isinstance(hit, dict) else hit.model_dump()
        metadata = hit_dict.get("metadata") or {}
        data_id = metadata.get("data_id")
        if data_id:
            result = await cognee.forget(data_id=data_id, dataset=DATASET_NAME)
            return {"status": "forgotten", "target": req.target, **result}

    return {"status": "not_found", "target": req.target}
