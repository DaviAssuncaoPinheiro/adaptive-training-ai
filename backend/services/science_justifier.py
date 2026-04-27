"""Bridges the microcycle generator and the RAG science agent.

Takes a freshly generated microcycle plan, picks a representative rep range
and goal, and asks the science agent for a PubMed-grounded justification with
APA citations. Failures are swallowed (returns None) so the microcycle can
still be persisted with the LLM-authored fallback text.
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

from rag.live_science_agent import build_live_science_agent
from routers.rag_router import _OLLAMA_ERROR_RE
from schemas.microcycle import MicrocycleSchema

logger = logging.getLogger(__name__)

_agent_singleton = None


def _get_agent():
    global _agent_singleton
    if _agent_singleton is None:
        _agent_singleton = build_live_science_agent()
    return _agent_singleton


def build_justification(*, profile: dict[str, Any], plan: MicrocycleSchema) -> str | None:
    rep_range = _representative_rep_range(plan)
    if rep_range is None:
        return None

    prompt = (
        "Justifique cientificamente a prescrição abaixo usando APENAS a base "
        "de conhecimento. Cite em APA inline e inclua a seção References ao "
        "final. Se a base não cobrir um ponto, diga isso explicitamente.\n"
        f"- Objetivo: {profile.get('primary_goal')}\n"
        f"- Nível: {profile.get('fitness_level')}\n"
        f"- Range de repetições predominante: {rep_range}\n"
        f"- RPE máximo do microciclo: {plan.max_rpe_cap}\n"
        f"- Volume semanal alvo por grupo muscular: {plan.max_weekly_sets_per_muscle} séries"
    )

    try:
        response = _get_agent().run(prompt)
    except Exception:  # noqa: BLE001
        logger.warning("science agent failed; falling back to LLM justification", exc_info=True)
        return None

    text = getattr(response, "content", None) or str(response)
    if not text or _OLLAMA_ERROR_RE.search(text):
        logger.warning("science agent returned empty/error content; falling back")
        return None
    return text


def _representative_rep_range(plan: MicrocycleSchema) -> str | None:
    counter: Counter[str] = Counter()
    for workout in plan.workouts:
        for ex in workout.exercises:
            value = (ex.target_reps or "").strip()
            if re.match(r"^\d+(-\d+)?$", value):
                counter[value] += 1
    if not counter:
        return None
    return counter.most_common(1)[0][0]
