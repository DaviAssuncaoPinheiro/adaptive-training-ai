from __future__ import annotations

from pathlib import Path

from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb

DEFAULT_PERSIST_DIR: Path = Path(__file__).resolve().parent.parent / "chroma_data"
DEFAULT_COLLECTION: str = "pubmed_fulltext"
EMBEDDING_MODEL_ID: str = "nomic-embed-text"


def build_embedder() -> OllamaEmbedder:
    """Force embeddings to run on the local Ollama instance.

    The 768-dim `nomic-embed-text` model is deliberate: it fits the default
    ChromaDB HNSW config and avoids shipping any cloud-hosted embedder.
    """
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
