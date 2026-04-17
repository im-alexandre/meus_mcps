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
DEFAULT_OLLAMA_PORT = 11434
_ollama_clients: dict[int, ollama.Client] = {}


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


MAX_EMBED_CHARS = 4000  # limite conservador para o modelo de embedding
CHUNK_OVERLAP = 200


def _get_ollama_client(port: int = DEFAULT_OLLAMA_PORT) -> ollama.Client:
    client = _ollama_clients.get(port)
    if client is None:
        client = ollama.Client(host=f"http://localhost:{port}")
        _ollama_clients[port] = client
    return client


def _embed(text: str, port: int = DEFAULT_OLLAMA_PORT) -> list[float]:
    client = _get_ollama_client(port)
    return client.embeddings(model="embeddinggemma", prompt=text)["embedding"]


def _split_chunks(text: str, max_chars: int = MAX_EMBED_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto em chunks com sobreposição. Retorna lista com 1 item se couber."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start += max_chars - overlap
    return chunks


# ── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool()
def index_csv(csv_path: str, port: int = DEFAULT_OLLAMA_PORT) -> str:
    """Indexa um CSV Scopus no ChromaDB. Espera colunas: Title, Abstract, Author Keywords, Authors, Year, Source title, DOI."""
    col = _get_collection()
    path = Path(csv_path)
    if not path.exists():
        return f"Arquivo nao encontrado: {csv_path}"

    csv.field_size_limit(10_000_000)
    added = 0
    chunks_total = 0
    ids, docs, metas, embeddings = [], [], [], []

    def _flush():
        if ids:
            col.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
            ids.clear(); docs.clear(); metas.clear(); embeddings.clear()

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            title = row.get("Title", "").strip()
            abstract = row.get("Abstract", "").strip()
            keywords = row.get("Author Keywords", "").strip()
            if not title:
                continue

            base_id = row.get("DOI", "").strip() or f"row-{i}"
            meta = {
                "title": title,
                "authors": row.get("Authors", ""),
                "year": row.get("Year", ""),
                "source": row.get("Source title", ""),
                "doi": row.get("DOI", ""),
                "keywords": keywords,
            }

            full_text = f"{title}. {abstract} {keywords}".strip()
            chunks = _split_chunks(full_text)

            for c_idx, chunk in enumerate(chunks):
                chunk_id = base_id if len(chunks) == 1 else f"{base_id}__chunk{c_idx}"
                ids.append(chunk_id)
                docs.append(chunk)
                metas.append(meta)
                embeddings.append(_embed(chunk, port=port))
                chunks_total += 1

                if len(ids) >= 50:
                    _flush()

            added += 1

    _flush()
    msg = f"Indexados {added} registros ({chunks_total} chunks) de {csv_path}"
    if chunks_total > added:
        msg += f" — {chunks_total - added} chunks extras por abstracts longos"
    return msg


@mcp.tool()
def search(query: str, top_k: int = 5, port: int = DEFAULT_OLLAMA_PORT) -> list[dict]:
    """Busca semantica no indice Scopus. Retorna os top_k resultados mais relevantes."""
    col = _get_collection()
    if col.count() == 0:
        return [{"error": "Indice vazio. Execute index_csv primeiro."}]

    results = col.query(
        query_embeddings=[_embed(query, port=port)],
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
