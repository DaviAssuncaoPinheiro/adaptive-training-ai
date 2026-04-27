from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from rag.knowledge_manager import ensure_knowledge
from rag.reference_cache import ReferenceCache
from rag.science_agent import build_science_agent
from rag.vector_store import build_knowledge_base

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rag"])

_CACHE_PATH = Path(__file__).resolve().parent.parent / "reference_cache.json"

# Ollama / Agno sometimes return HTTP-level errors as plain-text content
# instead of raising a Python exception.  Caching those would poison the store.
_OLLAMA_ERROR_RE = re.compile(
    r"(status[ _]code:\s*[45]\d{2})"
    r"|model .+ not found"
    r"|does not support tools",
    re.IGNORECASE,
)


class RagQuery(BaseModel):
    goal: str = Field(..., description="Primary training goal, e.g. 'hypertrophy'")
    rep_range: str = Field(..., description="Prescribed rep range, e.g. '8-12'")
    load_pct: float | None = Field(None, ge=0, le=100)
    notes: str | None = None


class Reference(BaseModel):
    title: str
    authors: list[str]
    journal: str
    pmcid: str
    year: int | None = None


class JustificationResponse(BaseModel):
    justification: str
    references: list[Reference]
    cached: bool


class SearchHit(BaseModel):
    passage: str
    pmcid: str | None = None
    title: str | None = None
    score: float | None = None


@lru_cache(maxsize=1)
def _default_knowledge_base():
    return build_knowledge_base()


def get_knowledge_base():
    return _default_knowledge_base()


@lru_cache(maxsize=1)
def _default_agent():
    return build_science_agent(knowledge_base=_default_knowledge_base())


def get_agent():
    return _default_agent()


def get_cache() -> ReferenceCache:
    return ReferenceCache(_CACHE_PATH)


@router.post("/justification", response_model=JustificationResponse)
def post_justification(
    payload: RagQuery,
    cache: ReferenceCache = Depends(get_cache),
    agent=Depends(get_agent),
    kb=Depends(get_knowledge_base),
) -> JustificationResponse:
    key = cache.make_key(payload.model_dump())
    cached = cache.get(key)
    if cached is not None:
        return JustificationResponse(**cached, cached=True)

    ensure_knowledge(query=payload.goal, knowledge_base=kb)

    try:
        response = agent.run(_build_prompt(payload))
    except Exception as exc:  # noqa: BLE001
        # Keep stack traces server-side; surface a safe generic error.
        raise HTTPException(status_code=502, detail="science agent unavailable") from exc

    justification_text = getattr(response, "content", str(response))

    # Guard: Agno may return Ollama HTTP errors as plain content instead
    # of raising.  Never cache these — surface them as 502 immediately.
    if _OLLAMA_ERROR_RE.search(justification_text or ""):
        logger.error("Ollama returned an error instead of a completion: %s", justification_text)
        raise HTTPException(status_code=502, detail="science agent returned an upstream error")

    references = _extract_references(response)

    stored: dict[str, Any] = {
        "justification": justification_text,
        "references": [r.model_dump() for r in references],
    }
    cache.set(key, stored)
    return JustificationResponse(**stored, cached=False)


@router.get("/search", response_model=list[SearchHit])
def get_search(
    query: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
    kb=Depends(get_knowledge_base),
) -> list[SearchHit]:
    try:
        results = kb.search(query=query, max_results=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="vector store unavailable") from exc

    hits: list[SearchHit] = []
    for r in results:
        meta = getattr(r, "meta_data", {}) or {}
        hits.append(
            SearchHit(
                passage=getattr(r, "content", ""),
                pmcid=meta.get("pmcid"),
                title=meta.get("title"),
                score=getattr(r, "score", None),
            )
        )
    return hits


def _build_prompt(q: RagQuery) -> str:
    lines = [
        "Justifique cientificamente a prescrição abaixo usando APENAS a base de conhecimento.",
        f"- Objetivo: {q.goal}",
        f"- Range de repetições: {q.rep_range}",
    ]
    if q.load_pct is not None:
        lines.append(f"- Carga alvo: {q.load_pct}% 1RM")
    if q.notes:
        lines.append(f"- Notas adicionais: {q.notes}")
    return "\n".join(lines)


def _extract_references(response: Any) -> list[Reference]:
    """Best-effort reference extraction from the Agno response.

    Agno exposes retrieved chunks on `response.references` (list of dicts with
    a `meta_data` key) in current versions. If the shape differs, we fall back
    to an empty list — the text-level APA citations stay in `justification`.
    """
    raw = getattr(response, "references", None) or []
    seen: set[str] = set()
    out: list[Reference] = []
    for item in raw:
        meta = item.get("meta_data") if isinstance(item, dict) else getattr(item, "meta_data", None)
        if not meta:
            continue
        pmcid = meta.get("pmcid") or ""
        if not pmcid or pmcid in seen:
            continue
        seen.add(pmcid)
        out.append(
            Reference(
                title=meta.get("title", ""),
                authors=list(meta.get("authors", []) or []),
                journal=meta.get("journal", ""),
                pmcid=pmcid,
                year=meta.get("year"),
            )
        )
    if raw and not out:
        # Agno had hits but none surfaced usable metadata — likely a response-
        # shape drift after an upgrade. Surface it so we notice before prod.
        logger.warning(
            "response.references had %d item(s) but none yielded metadata — Agno shape may have drifted",
            len(raw),
        )
    return out
