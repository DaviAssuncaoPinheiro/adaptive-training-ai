from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from agno.knowledge.embedder.base import Embedder
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb

DEFAULT_PERSIST_DIR: Path = Path(__file__).resolve().parent.parent / "chroma_data"
DEFAULT_COLLECTION: str = "pubmed_fulltext"
EMBEDDING_MODEL_ID: str = "nomic-embed-text"
GEMINI_EMBEDDING_MODEL_ID: str = "gemini-embedding-2"
GEMINI_EMBEDDING_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"


class GeminiRestEmbedder(Embedder):
    """Small REST embedder so Gemini can be used without removing Ollama."""

    def __init__(self, *, model: str, api_key: str, dimensions: int = 768) -> None:
        super().__init__(dimensions=dimensions)
        self.id = model
        self.api_key = api_key

    def _payload(self, text: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": f"models/{self.id}",
            "content": {"parts": [{"text": text}]},
        }
        if self.dimensions:
            payload["output_dimensionality"] = self.dimensions
        return payload

    def _extract(self, data: dict[str, Any]) -> list[float]:
        values = data.get("embedding", {}).get("values", [])
        return values if isinstance(values, list) else []

    def get_embedding(self, text: str) -> list[float]:
        response = httpx.post(
            GEMINI_EMBEDDING_ENDPOINT.format(model=self.id),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            json=self._payload(text),
            timeout=60,
        )
        response.raise_for_status()
        return self._extract(response.json())

    def get_embedding_and_usage(self, text: str):
        return self.get_embedding(text), None

    async def async_get_embedding(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                GEMINI_EMBEDDING_ENDPOINT.format(model=self.id),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=self._payload(text),
            )
        response.raise_for_status()
        return self._extract(response.json())

    async def async_get_embedding_and_usage(self, text: str):
        return await self.async_get_embedding(text), None


def build_embedder() -> Embedder:
    """Force embeddings to run on the local Ollama instance.

    The 768-dim `nomic-embed-text` model is deliberate: it fits the default
    ChromaDB HNSW config and avoids shipping any cloud-hosted embedder.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "ollama").strip().lower()
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured for embeddings")
        dimensions = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768"))
        return GeminiRestEmbedder(
            model=os.getenv("GEMINI_EMBEDDING_MODEL_ID", GEMINI_EMBEDDING_MODEL_ID),
            api_key=api_key,
            dimensions=dimensions,
        )
    return OllamaEmbedder(id=EMBEDDING_MODEL_ID, dimensions=768)


def build_knowledge_base(
    persist_dir: Path | None = None,
    collection: str = DEFAULT_COLLECTION,
) -> Knowledge:
    path = persist_dir or DEFAULT_PERSIST_DIR
    path.mkdir(parents=True, exist_ok=True)

    vector_db = ChromaDb(
        collection=collection,
        path=str(path),
        persistent_client=True,
        embedder=build_embedder(),
    )
    return Knowledge(vector_db=vector_db)
