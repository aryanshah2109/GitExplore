"""Repository query service."""

from __future__ import annotations

from backend.api.schemas.query import JudgementSchema, QueryResponse
from backend.api.services.ingest_service import SESSION_STORE


def run_query(repo_id: str, query: str) -> QueryResponse:
    """Run a query against an ingested repository."""
    from backend.app.rag.pipeline import RAGPipeline

    if repo_id not in SESSION_STORE:
        raise KeyError(repo_id)

    repo_session = SESSION_STORE[repo_id]
    rag = repo_session.get("rag")
    if rag is None:
        rag = RAGPipeline(repo_session["chunks"], repo_id)
        repo_session["rag"] = rag

    result = rag.query(query)
    judgement = result.get("judgement") or {}

    return QueryResponse(
        answer=result.get("answer") or "",
        query_type=result.get("query_type") or "unknown",
        judgement=JudgementSchema(
            faithfulness=int(judgement.get("faithfulness", 0)),
            retrieval_relevance=int(judgement.get("retrieval_relevance", 0)),
            citation_accuracy=int(judgement.get("citation_accuracy", 0)),
            query_type_fit=int(judgement.get("query_type_fit", 0)),
            reasoning=str(judgement.get("reasoning", "")),
        ),
        citation_validation=result.get("citation_validation") or {},
        status=result.get("status") or "ok",
    )


def clear_session(repo_id: str) -> None:
    """Clear the stored conversation history for a repo."""
    if repo_id not in SESSION_STORE:
        raise KeyError(repo_id)
    rag = SESSION_STORE[repo_id].get("rag")
    if rag is not None:
        rag.clear_session()
