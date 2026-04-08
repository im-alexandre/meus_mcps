"""MCP Server — Busca semântica no CSV Scopus via ChromaDB + nomic-embed-text."""

import csv
import os
from pathlib import Path

import chromadb
import ollama
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("scopus-search")

CHROMA_DIR = os.environ.get("CHROMA_DIR", "./chroma_data")
COLLECTION_NAME = "scopus"

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _embed(text: str) -> list[float]:
    return ollama.embeddings(model="nomic-embed-text", prompt=text)["embedding"]


# ── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool()
def index_csv(csv_path: str) -> str:
    """Indexa um CSV Scopus no ChromaDB. Espera colunas: Title, Abstract, Author Keywords, Authors, Year, Source title, DOI."""
    col = _get_collection()
    path = Path(csv_path)
    if not path.exists():
        return f"Arquivo nao encontrado: {csv_path}"

    added = 0
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        ids, docs, metas, embeddings = [], [], [], []
        for i, row in enumerate(reader):
            title = row.get("Title", "").strip()
            abstract = row.get("Abstract", "").strip()
            keywords = row.get("Author Keywords", "").strip()
            if not title:
                continue

            text = f"{title}. {abstract} {keywords}".strip()
            doc_id = row.get("DOI", "").strip() or f"row-{i}"

            ids.append(doc_id)
            docs.append(text)
            metas.append({
                "title": title,
                "authors": row.get("Authors", ""),
                "year": row.get("Year", ""),
                "source": row.get("Source title", ""),
                "doi": row.get("DOI", ""),
                "keywords": keywords,
            })
            embeddings.append(_embed(text))
            added += 1

            # batch upsert a cada 50
            if len(ids) >= 50:
                col.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
                ids, docs, metas, embeddings = [], [], [], []

        if ids:
            col.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

    return f"Indexados {added} registros de {csv_path}"


@mcp.tool()
def search(query: str, top_k: int = 5) -> list[dict]:
    """Busca semantica no indice Scopus. Retorna os top_k resultados mais relevantes."""
    col = _get_collection()
    if col.count() == 0:
        return [{"error": "Indice vazio. Execute index_csv primeiro."}]

    results = col.query(
        query_embeddings=[_embed(query)],
        n_results=min(top_k, col.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        score = 1 - dist  # cosine distance -> similarity
        output.append({
            "score": round(score, 4),
            "title": meta.get("title", ""),
            "authors": meta.get("authors", ""),
            "year": meta.get("year", ""),
            "doi": meta.get("doi", ""),
            "source": meta.get("source", ""),
            "snippet": doc[:300],
        })
    return output


@mcp.tool()
def collection_stats() -> dict:
    """Retorna estatisticas da collection Scopus."""
    col = _get_collection()
    return {"collection": COLLECTION_NAME, "count": col.count()}


if __name__ == "__main__":
    mcp.run()