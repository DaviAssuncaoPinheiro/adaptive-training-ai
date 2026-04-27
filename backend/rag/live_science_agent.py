"""Science agent backed by live PubMed search (no pre-ingested knowledge base).

Uses Agno's `PubmedTools` so the agent searches PubMed at runtime instead of
querying the local ChromaDB. Trade-off: ~5–10s extra per generation, but zero
manual ingestion ever.
"""
from __future__ import annotations

import os

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.pubmed import PubmedTools

LLM_MODEL_ID = "llama3.1"

SYSTEM_PROMPT = (
    "You are a sports-science assistant that justifies resistance-training "
    "prescriptions for an adaptive coaching system.\n\n"
    "Hard rules — these are non-negotiable:\n"
    "1. You MUST call the `search_pubmed` tool to retrieve evidence before "
    "writing the justification. Use 1 to 3 focused queries derived from the "
    "user's goal, level and prescription parameters.\n"
    "2. Base every claim strictly on the abstracts returned by the tool. If "
    "no relevant abstract was returned, say so explicitly — do NOT fabricate, "
    "extrapolate, or rely on prior training data.\n"
    "3. Cite every supporting study inline in APA style using the metadata in "
    "the tool response (authors, year). Example: (Smith & Doe, 2023).\n"
    "4. End the response with a 'References' section listing the full APA "
    "reference for each citation.\n"
    "5. Never invent authors, year, or journal. Omit a reference rather than "
    "guessing.\n"
    "6. Write in clear, professional Portuguese (PT-BR), but keep citation "
    "formatting in APA English conventions."
)


def build_live_science_agent() -> Agent:
    email = os.environ.get("NCBI_ENTREZ_EMAIL", "noreply@example.com")
    return Agent(
        model=Ollama(id=LLM_MODEL_ID),
        tools=[PubmedTools(email=email, max_results=5)],
        description="Live PubMed-backed scientific-justification agent.",
        instructions=[SYSTEM_PROMPT],
        markdown=True,
    )
