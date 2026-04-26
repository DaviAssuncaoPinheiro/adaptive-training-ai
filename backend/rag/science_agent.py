from __future__ import annotations

from agno.agent import Agent
from agno.knowledge import Knowledge
from agno.models.ollama import Ollama

LLM_MODEL_ID = "llama3.1"

SYSTEM_PROMPT = (
    "You are a sports-science assistant that justifies resistance-training "
    "prescriptions for an adaptive coaching system.\n\n"
    "Hard rules — these are non-negotiable:\n"
    "1. You MUST base every claim strictly on passages retrieved from the "
    "knowledge base. If the knowledge base does not support a claim, say so "
    "explicitly and do NOT invent, extrapolate, or rely on prior training data.\n"
    "2. Cite every supporting passage inline in APA style using the article "
    "metadata (authors, year). Example: (Smith & Doe, 2023).\n"
    "3. At the end of every response, include a 'References' section listing "
    "the full APA reference for each source you cited.\n"
    "4. Never guess authors, year, or journal. If a metadata field is missing, "
    "omit the reference rather than fabricating it.\n"
    "5. Write in clear, professional Portuguese (the coach reads PT-BR), but "
    "keep citation formatting in APA English conventions."
)


def build_science_agent(knowledge_base: Knowledge) -> Agent:
    return Agent(
        model=Ollama(id=LLM_MODEL_ID),
        knowledge=knowledge_base,
        search_knowledge=True,
        description="Scientific-justification agent for adaptive training plans.",
        instructions=[SYSTEM_PROMPT],
        markdown=True,
    )
