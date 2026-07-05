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
    list_mode: bool = False


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


def _matches_filters(text: str, filters: dict[str, Any]) -> bool:
    """Exact-match every filter as a literal `key=value` substring in the stored tag line."""
    return all(f"{k}={v}".lower() in text.lower() for k, v in filters.items())


@app.post("/recall")
async def recall(req: RecallRequest):
    """Query the graph.

    list_mode=True switches to SearchType.CHUNKS instead of the default
    GRAPH_COMPLETION. GRAPH_COMPLETION synthesizes one LLM answer from all
    matching facts — great for a single lookup (agent why), but it silently
    collapses multiple matching tasks into one sentence, which breaks
    commands that need every match (agent assigned, agent workspace). CHUNKS
    returns the raw matching chunks instead, one per stored fact.

    Filters are folded into the query text for GRAPH_COMPLETION (which
    reasons over them), but CHUNKS does pure embedding similarity and
    mostly ignores a text prefix — so in list_mode, filters are instead
    applied as an exact `key=value` substring check against each chunk's
    text (which still carries the `[agent=x type=y ...]` tag line
    /remember wrote), rather than relying on semantic similarity to filter.
    """
    query = req.query
    if req.filters and not req.list_mode:
        query = " ".join(f"{k}={v}" for k, v in req.filters.items()) + " " + query

    kwargs: dict[str, Any] = {"datasets": [DATASET_NAME], "top_k": req.top_k}
    if req.list_mode:
        kwargs["query_type"] = SearchType.CHUNKS
        kwargs["top_k"] = max(req.top_k, 50)  # over-fetch since filtering happens after
    results = await cognee.recall(query, **kwargs)

    dicts = [r.model_dump() if hasattr(r, "model_dump") else r for r in results]
    if req.list_mode and req.filters:
        dicts = [d for d in dicts if _matches_filters(d.get("text") or "", req.filters)]
    return {"results": dicts[: req.top_k]}


@app.post("/improve")
async def improve(req: ImproveRequest):
    """Enrich the knowledge graph.

    Tries the real improve() first (triplet-embedding enrichment). This
    tenant's Cognee Cloud build doesn't expose /api/v1/improve yet (verified
    against its own /openapi.json — /api/v1/cognify is present, /improve is
    not), so on a 404 we fall back to cognify() on the same dataset: it's the
    underlying pipeline improve() itself calls for entity/relationship
    re-extraction and re-indexing, exposed on this tenant, and cheap to call
    since cognify() is incremental (skips already-processed data). This is
    real enrichment either way, not a no-op — the primary improve() lifecycle
    coverage for this project remains the Claude Code plugin's automatic
    SessionEnd hook (see docs/architecture.md); this endpoint is the manual
    trigger for the other agents.
    """
    kwargs: dict[str, Any] = {"dataset": DATASET_NAME}
    if req.session_id:
        kwargs["session_ids"] = [req.session_id]
    try:
        result = await cognee.improve(**kwargs)
        return {"status": "completed", "mode": "improve", "raw": str(result)}
    except RuntimeError as exc:
        if "404" not in str(exc):
            raise

    result = await cognee.cognify(datasets=[DATASET_NAME])
    return {"status": "completed", "mode": "cognify_fallback", "raw": str(result)}


def _first_data_id(hits: list) -> Optional[str]:
    for hit in hits:
        # Remote mode (cognee.serve) returns plain dicts from the cloud API;
        # local-SDK mode returns SearchResultItem objects — handle both.
        hit_dict = hit if isinstance(hit, dict) else hit.model_dump()
        metadata = hit_dict.get("metadata") or {}
        data_id = metadata.get("data_id")
        if data_id:
            return data_id
    return None


@app.post("/forget")
async def forget(req: ForgetRequest):
    """Find the data item whose stored text mentions `target`, then forget it.

    cognee.forget() only deletes by data_id/dataset/everything — it has no
    text-query form. So we resolve target -> data_id via a chunk recall,
    whose payload carries the source data_id in metadata (works in both
    local and Cognee Cloud remote mode; local-disk reads of raw_data_location
    would not, since that path lives on the cloud tenant, not this machine).

    ponytail: this tenant's CHUNKS/CHUNKS_LEXICAL are both embedding-
    similarity search, not literal keyword match (verified directly against
    the tenant API — a short slug like "retry-loop-verification" isn't
    surfaced even at top_k=40 across a ~30-item dataset, despite being the
    only item containing that exact text). So `target` must be phrased
    close to the stored sentence for either search type to surface it —
    natural-language targets (e.g. "Stripe webhook signature validation")
    work reliably; arbitrary CLI-arg slugs may not. Upgrade path if this
    matters more: track data_id per remembered item in a local sidecar
    index instead of relying on recall to find it.
    """
    for query_type in (SearchType.CHUNKS, SearchType.CHUNKS_LEXICAL):
        data_id = _first_data_id(
            await cognee.recall(req.target, query_type=query_type, datasets=[DATASET_NAME], top_k=10)
        )
        if data_id:
            result = await cognee.forget(data_id=data_id, dataset=DATASET_NAME)
            return {"status": "forgotten", "target": req.target, **result}

    return {"status": "not_found", "target": req.target}
