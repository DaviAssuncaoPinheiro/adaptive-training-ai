"""ETL: PubMed Central Open-Access full text → ChromaDB knowledge base.

Designed to be runnable as a module:

    python -m rag.pubmed_ingestor --query "resistance training volume hypertrophy" --max 25

We deliberately use the raw NCBI E-utilities (via Biopython's `Entrez`) rather
than higher-level wrappers: we only need esearch + efetch, and the XML schema
for OA full text is stable. Staying close to the bytes keeps the failure modes
obvious (HTTP error vs. parse error vs. non-OA record).
"""
from __future__ import annotations

import argparse
import logging
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Protocol

import defusedxml.ElementTree as DefusedET  # type: ignore[import-untyped]
from Bio import Entrez  # type: ignore[import-untyped]
from agno.knowledge.document.base import Document

from rag.vector_store import build_knowledge_base

logger = logging.getLogger(__name__)

# NCBI rate limit without API key is 3 req/s; 0.34s between calls stays inside
# that budget with a small margin. With an API key the limit rises to 10/s.
_DEFAULT_ENTREZ_EMAIL = "dgap.snf23@uea.edu.br"
_RATE_LIMIT_DELAY_NO_KEY = 0.34
_RATE_LIMIT_DELAY_WITH_KEY = 0.1


def _configure_entrez() -> float:
    """Apply Entrez auth from env vars, return the per-request delay to use."""
    Entrez.email = os.getenv("NCBI_ENTREZ_EMAIL", _DEFAULT_ENTREZ_EMAIL)
    api_key = os.getenv("NCBI_API_KEY")
    if api_key:
        Entrez.api_key = api_key
        return _RATE_LIMIT_DELAY_WITH_KEY
    return _RATE_LIMIT_DELAY_NO_KEY


@dataclass(frozen=True)
class Article:
    pmcid: str
    title: str
    authors: list[str]
    journal: str
    year: int | None
    body: str


class KnowledgeBaseLike(Protocol):
    """Matches Agno's Knowledge: exposes a vector_db with upsert(content_hash, documents)."""
    vector_db: Any


def parse_pmc_xml(xml_text: str) -> Article:
    # defusedxml hardens against XML bombs / XXE. PMC is trusted but this is
    # cheap defense-in-depth and eliminates a Bandit finding on the import.
    root = DefusedET.fromstring(xml_text)
    article_el = root.find(".//article") if root.tag != "article" else root
    if article_el is None:
        raise ValueError("no <article> element in PMC response")

    pmcid = _find_text(article_el, ".//article-id[@pub-id-type='pmc']") or ""
    if pmcid and not pmcid.startswith("PMC"):
        pmcid = f"PMC{pmcid}"

    title = _find_text(article_el, ".//title-group/article-title") or ""
    journal = _find_text(article_el, ".//journal-title") or ""
    year_text = _find_text(article_el, ".//pub-date/year")
    year = int(year_text) if year_text and year_text.isdigit() else None

    authors: list[str] = []
    for contrib in article_el.findall(".//contrib-group/contrib"):
        surname = _find_text(contrib, ".//surname") or ""
        given = _find_text(contrib, ".//given-names") or ""
        full = f"{given} {surname}".strip()
        if full:
            authors.append(full)

    body_parts: list[str] = []
    for p in article_el.findall(".//body//p"):
        text = "".join(p.itertext()).strip()
        if text:
            body_parts.append(text)
    body = "\n\n".join(body_parts)

    return Article(
        pmcid=pmcid,
        title=title,
        authors=authors,
        journal=journal,
        year=year,
        body=body,
    )


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    step = chunk_size - overlap
    if step <= 0:
        raise ValueError("overlap must be smaller than chunk_size")
    # Only emit a chunk starting at position i if i < len(text) - overlap,
    # which ensures the chunk contributes content not already covered by the
    # previous chunk's overlap region. This prevents tiny tail fragments.
    return [
        text[i : i + chunk_size]
        for i in range(0, len(text), step)
        if i < len(text) - overlap
    ]


def fetch_open_access_articles(query: str, max_results: int) -> list[Article]:
    """Search PMC for OA full text and download each matching article."""
    delay = _configure_entrez()
    search_handle = Entrez.esearch(
        db="pmc",
        term=f'{query} AND "open access"[filter]',
        retmax=max_results,
    )
    search_result = Entrez.read(search_handle)
    search_handle.close()
    ids: list[str] = search_result.get("IdList", [])
    logger.info("PMC esearch matched %d records", len(ids))

    articles: list[Article] = []
    for idx, pmc_id in enumerate(ids):
        # Pace requests to stay under NCBI's rate limit (see module constants).
        if idx > 0:
            time.sleep(delay)
        try:
            fetch_handle = Entrez.efetch(db="pmc", id=pmc_id, rettype="full", retmode="xml")
            xml_text = fetch_handle.read()
            if isinstance(xml_text, bytes):
                xml_text = xml_text.decode("utf-8", errors="replace")
            fetch_handle.close()
            article = parse_pmc_xml(xml_text)
            if article.body:
                articles.append(article)
        except Exception:  # noqa: BLE001 — one bad record must not abort the run.
            logger.exception("skipping PMC id=%s", pmc_id)
    return articles


def run_ingestion(
    query: str,
    max_results: int,
    knowledge_base: KnowledgeBaseLike | None = None,
) -> int:
    """Fetch, chunk, and upsert PMC articles into the vector DB. Returns chunk count."""
    kb = knowledge_base or build_knowledge_base()
    articles = fetch_open_access_articles(query, max_results)
    total_chunks = 0
    for article in articles:
        docs = _article_to_documents(article)
        if not docs:
            continue
        # One upsert call per article — PMCID is the stable content_hash.
        kb.vector_db.upsert(content_hash=article.pmcid, documents=docs)
        total_chunks += len(docs)
    logger.info("ingested %d chunks from %d articles", total_chunks, len(articles))
    return total_chunks


def _article_to_documents(article: Article) -> list[Document]:
    docs: list[Document] = []
    for idx, chunk in enumerate(chunk_text(article.body)):
        docs.append(
            Document(
                name=f"{article.pmcid}-{idx}",
                content=chunk,
                meta_data={
                    "pmcid": article.pmcid,
                    "title": article.title,
                    "authors": article.authors,
                    "journal": article.journal,
                    "year": article.year,
                    "chunk_index": idx,
                },
            )
        )
    return docs


def _find_text(element: ET.Element, path: str) -> str | None:
    found = element.find(path)
    if found is None:
        return None
    text = "".join(found.itertext()).strip()
    return text or None


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Ingest PMC Open-Access articles into the RAG store")
    parser.add_argument("--query", required=True, help="PubMed search term")
    parser.add_argument("--max", type=int, default=25, help="maximum number of articles to fetch")
    args = parser.parse_args()
    run_ingestion(query=args.query, max_results=args.max)


if __name__ == "__main__":
    main()
