"""
Quick smoke test: embed a query and retrieve top-k chunks from Qdrant.

Usage:
    python -m scripts.run_query
"""

import ollama
from qdrant_client.models import Filter, FieldCondition, MatchValue

from backend.app.core.config_loader import config
from backend.app.core.qdrant_setup import client
from backend.app.core.logger import get_logger

from pprint import pprint

logger = get_logger()


COLLECTION = config.vector_db.collection_name
EMBED_MODEL = config.embedding.model_name
TOP_K = config.vector_db.top_k


def embed_query(text: str) -> list[float]:
    response = ollama.embed(model=EMBED_MODEL, input=[text])
    return response["embeddings"][0]


def search(query: str, repo_id: str = None, chunk_type: str = None) -> list[dict]:

    query_vector = embed_query(query)

    conditions = []

    if repo_id:
        conditions.append(
            FieldCondition(key="repo_id", match=MatchValue(value=repo_id))
        )

    if chunk_type:
        conditions.append(
            FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type))
        )

    search_filter = Filter(must=conditions) if conditions else None

    results = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=TOP_K,
        query_filter=search_filter,
        with_payload=True
    )

    return results


def get_context(query: str, repo_id: str, top_k: int = 5) -> str:

    results = search(query=query, repo_id=repo_id)
    top_results = results[:top_k]

    blocks = []

    for i, result in enumerate(results[:top_k], 1):
        p = result.payload

        header = (
            f"[{i}] {p.get('file_path', p.get('module_path', 'unknown'))} | "
            f"{p.get('chunk_type')} | "
            f"{p.get('symbol')} | "
            f"Lines {p.get('start_line')}-{p.get('end_line')} | "
            f"Score: {result.score:.3f}"
        )

        code = p.get('code', '[code not available]')

        blocks.append(f"{header}\n{'─'*50}\n{code}")

    return "\n\n".join(blocks)
            

get_context("How model is evaluated?", "265dc296-f7f0-4ec9-906d-d2a30a27189e")