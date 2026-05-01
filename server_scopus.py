"""MCP Server — Busca semântica em acervos Scopus via ChromaDB + Ollama."""

import csv
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import chromadb
import ollama
import rispy

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("scopus-search")

CHROMA_DIR = os.environ.get("CHROMA_DIR", "./chroma_data")
DEFAULT_HOST = os.environ.get("HOST", "").strip() or "http://localhost"
DEFAULT_PORT = int(os.environ.get("PORT", "").strip() or "11434")
DEFAULT_MODEL = os.environ.get("MODEL", "").strip() or "embeddinggemma"

_client: chromadb.ClientAPI | None = None
_collections: dict[str, chromadb.Collection] = {}
_ollama_clients: dict[str, ollama.Client] = {}


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


def _normalize_collection_name(collection: str, allow_new: bool = True) -> str:
    name = collection.strip()
    if not name:
        raise ValueError(_missing_collection_message(allow_new=allow_new))
    return name


def _collection_item_name(collection: object) -> str:
    return str(getattr(collection, "name", collection))


def _list_collection_names() -> list[str]:
    return sorted(_collection_item_name(item) for item in _get_client().list_collections())


def _format_available_collections() -> str:
    names = _list_collection_names()
    if not names:
        return "Nenhuma collection existente foi encontrada."
    return "Collections disponiveis: " + ", ".join(names) + "."


def _missing_collection_message(allow_new: bool = True) -> str:
    message = (
        "Informe explicitamente o parametro 'collection' na chamada da ferramenta. "
        f"{_format_available_collections()}"
    )
    if allow_new:
        message += " Para indexar, voce tambem pode informar uma nova collection."
    return message


def _get_or_create_collection(collection: str) -> chromadb.Collection:
    name = _normalize_collection_name(collection)
    cached = _collections.get(name)
    if cached is None:
        cached = _get_client().get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
        _collections[name] = cached
    return cached


def _get_existing_collection(collection: str) -> chromadb.Collection | None:
    name = _normalize_collection_name(collection, allow_new=False)
    cached = _collections.get(name)
    if cached is not None:
        return cached
    if name not in _list_collection_names():
        return None
    cached = _get_client().get_collection(name=name)
    _collections[name] = cached
    return cached


MAX_EMBED_CHARS = 4000  # limite conservador para o modelo de embedding
CHUNK_OVERLAP = 200


def _normalize_host(host: str, port: int = DEFAULT_PORT) -> str:
    host = host.strip()
    if not host:
        host = DEFAULT_HOST
    if "://" not in host:
        host = f"http://{host}"

    parsed = urlsplit(host)
    if parsed.port is not None:
        return host.rstrip("/")

    netloc = f"{parsed.hostname}:{port}"
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth = f"{auth}:{parsed.password}"
        netloc = f"{auth}@{netloc}"

    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, "")).rstrip("/")


def _get_ollama_client(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ollama.Client:
    normalized_host = _normalize_host(host, port)
    client = _ollama_clients.get(normalized_host)
    if client is None:
        client = ollama.Client(host=normalized_host)
        _ollama_clients[normalized_host] = client
    return client


def _embed(
    text: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    model: str = DEFAULT_MODEL,
) -> list[float]:
    client = _get_ollama_client(host, port)
    return client.embeddings(model=model.strip() or DEFAULT_MODEL, prompt=text)[
        "embedding"
    ]


def _split_chunks(
    text: str, max_chars: int = MAX_EMBED_CHARS, overlap: int = CHUNK_OVERLAP
) -> list[str]:
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


def _normalize_record(
    record: dict[str, str], fallback_id: str
) -> tuple[str, dict[str, str], str] | None:
    title = record.get("title", "").strip()
    if not title:
        return None

    abstract = record.get("abstract", "").strip()
    keywords = record.get("keywords", "").strip()
    base_id = record.get("doi", "").strip() or fallback_id
    meta = {
        "title": title,
        "authors": record.get("authors", ""),
        "year": record.get("year", ""),
        "source": record.get("source", ""),
        "doi": record.get("doi", ""),
        "keywords": keywords,
    }
    full_text = f"{title}. {abstract} {keywords}".strip()
    return base_id, meta, full_text


def _index_records(
    records: list[dict[str, str]],
    source_path: str,
    collection: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    model: str = DEFAULT_MODEL,
) -> str:
    collection_name = _normalize_collection_name(collection)
    col = _get_or_create_collection(collection_name)
    added = 0
    chunks_total = 0
    ids, docs, metas, embeddings = [], [], [], []

    def _flush():
        if ids:
            col.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
            ids.clear()
            docs.clear()
            metas.clear()
            embeddings.clear()

    for i, record in enumerate(records):
        normalized = _normalize_record(record, fallback_id=f"row-{i}")
        if normalized is None:
            continue

        base_id, meta, full_text = normalized
        chunks = _split_chunks(full_text)

        for c_idx, chunk in enumerate(chunks):
            chunk_id = base_id if len(chunks) == 1 else f"{base_id}__chunk{c_idx}"
            ids.append(chunk_id)
            docs.append(chunk)
            metas.append(meta)
            embeddings.append(_embed(chunk, host=host, port=port, model=model))
            chunks_total += 1

            if len(ids) >= 50:
                _flush()

        added += 1

    _flush()
    msg = (
        f"Indexados {added} registros ({chunks_total} chunks) de {source_path} "
        f"na collection {collection_name}"
    )
    if chunks_total > added:
        msg += f" — {chunks_total - added} chunks extras por abstracts longos"
    return msg


def _coerce_ris_field(value: object) -> str:
    if isinstance(value, list):
        return "; ".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def _read_ris_records(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig") as f:
        ris_entries = rispy.load(f)

    records: list[dict[str, str]] = []
    for entry in ris_entries:
        year = _coerce_ris_field(entry.get("year") or entry.get("publication_year"))
        records.append(
            {
                "title": _coerce_ris_field(
                    entry.get("title") or entry.get("primary_title")
                ),
                "abstract": _coerce_ris_field(entry.get("abstract")),
                "keywords": _coerce_ris_field(entry.get("keywords")),
                "authors": _coerce_ris_field(entry.get("authors")),
                "year": year[:4],
                "source": _coerce_ris_field(
                    entry.get("journal_name")
                    or entry.get("secondary_title")
                    or entry.get("periodical_name")
                ),
                "doi": _coerce_ris_field(entry.get("doi")),
            }
        )
    return records


# ── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool()
def index_csv(
    csv_path: str,
    collection: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    model: str = DEFAULT_MODEL,
) -> str:
    """Indexa um CSV Scopus na collection informada. Espera colunas: Title, Abstract, Author Keywords, Authors, Year, Source title, DOI."""
    try:
        collection_name = _normalize_collection_name(collection, allow_new=True)
    except ValueError as exc:
        return str(exc)

    path = Path(csv_path)
    if not path.exists():
        return f"Arquivo nao encontrado: {csv_path}"

    csv.field_size_limit(10_000_000)
    records: list[dict[str, str]] = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            records.append(
                {
                    "title": row.get("Title", ""),
                    "abstract": row.get("Abstract", ""),
                    "keywords": row.get("Author Keywords", ""),
                    "authors": row.get("Authors", ""),
                    "year": row.get("Year", ""),
                    "source": row.get("Source title", ""),
                    "doi": row.get("DOI", ""),
                }
            )

    return _index_records(
        records, csv_path, collection=collection_name, host=host, port=port, model=model
    )


@mcp.tool()
def index_ris(
    ris_path: str,
    collection: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Indexa um arquivo RIS na collection informada.
    Usa campos padrao como TI/T1, AB, KW, AU/A1, PY/Y1, JO/JF/T2
    e DO.
    """
    try:
        collection_name = _normalize_collection_name(collection, allow_new=True)
    except ValueError as exc:
        return str(exc)

    path = Path(ris_path)
    if not path.exists():
        return f"Arquivo nao encontrado: {ris_path}"

    records = _read_ris_records(path)
    return _index_records(
        records, ris_path, collection=collection_name, host=host, port=port, model=model
    )


@mcp.tool()
def search(
    query: str,
    collection: str,
    top_k: int = 5,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    model: str = DEFAULT_MODEL,
) -> list[dict]:
    """Busca semantica na collection informada. Retorna os top_k resultados mais relevantes."""
    try:
        collection_name = _normalize_collection_name(collection, allow_new=False)
    except ValueError as exc:
        return [{"error": str(exc)}]

    col = _get_existing_collection(collection_name)
    if col is None:
        return [
            {
                "error": (
                    f"Collection nao encontrada: {collection_name}. "
                    f"{_format_available_collections()}"
                )
            }
        ]

    if col.count() == 0:
        return [
            {
                "error": (
                    f"Indice vazio na collection {collection_name}. "
                    "Execute index_csv ou index_ris primeiro informando essa collection."
                )
            }
        ]

    results = col.query(
        query_embeddings=[_embed(query, host=host, port=port, model=model)],
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
        output.append(
            {
                "score": round(score, 4),
                "title": meta.get("title", ""),
                "authors": meta.get("authors", ""),
                "year": meta.get("year", ""),
                "doi": meta.get("doi", ""),
                "source": meta.get("source", ""),
                "snippet": doc[:300],
            }
        )
    return output


@mcp.tool()
def list_collections() -> dict:
    """Lista as collections disponiveis para indexacao ou busca."""
    return {"collections": _list_collection_names()}


@mcp.tool()
def collection_stats(collection: str) -> dict:
    """Retorna estatisticas da collection informada."""
    try:
        collection_name = _normalize_collection_name(collection, allow_new=False)
    except ValueError as exc:
        return {"error": str(exc)}

    col = _get_existing_collection(collection_name)
    if col is None:
        return {
            "error": (
                f"Collection nao encontrada: {collection_name}. "
                f"{_format_available_collections()}"
            )
        }
    return {"collection": collection_name, "count": col.count()}


if __name__ == "__main__":
    mcp.run()
