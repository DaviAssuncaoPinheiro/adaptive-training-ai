"""Lazy-ingestion helper for the science RAG pipeline.

The vector store is populated on demand: every request that needs grounded
evidence first checks whether the knowledge base already covers the query and,
if not, triggers a PubMed Open-Access ingestion before the agent runs. This
removes the need for any manual pre-ingestion step — the corpus grows
organically with usage and stays idempotent because `run_ingestion` upserts by
PMCID.
"""
from __future__ import annotations

import logging

from rag.pubmed_ingestor import run_ingestion

logger = logging.getLogger(__name__)

_INGESTION_MAX_RESULTS = 10


def ensure_knowledge(query: str, knowledge_base, min_chunks: int = 3) -> None:
    """Guarantee the KB has at least `min_chunks` hits for `query`.

    Searches first; only triggers a PubMed ingestion when coverage is below
    threshold. Failures are logged but never raised — the caller's agent will
    surface its own error if the KB is genuinely unusable.
    """
    if not query or not query.strip():
        return

    try:
        hits = knowledge_base.search(query=query, max_results=min_chunks)
    except Exception:  # noqa: BLE001 — empty/missing collection should fall through to ingestion
        logger.info("knowledge_base.search failed for %r — assuming empty store", query)
        hits = []

    if len(hits) >= min_chunks:
        logger.info("kb already has %d hit(s) for %r; skipping ingestion", len(hits), query)
        return

    logger.info(
        "kb has %d hit(s) for %r (< %d) — running PubMed ingestion",
        len(hits),
        query,
        min_chunks,
    )
    try:
        chunks = run_ingestion(
            query=query,
            max_results=_INGESTION_MAX_RESULTS,
            knowledge_base=knowledge_base,
        )
        logger.info("ingested %d new chunk(s) for %r", chunks, query)
    except Exception:  # noqa: BLE001
        logger.exception("PubMed ingestion failed for %r", query)
