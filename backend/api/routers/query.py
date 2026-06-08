"""Query router."""

from fastapi import APIRouter, HTTPException

from backend.api.schemas.query import QueryRequest, QueryResponse
from backend.api.services.query_service import clear_session, run_query

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_repo(request: QueryRequest) -> QueryResponse:
    """Run a question over an ingested repository."""
    try:
        return run_query(request.repo_id, request.query)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="repo_id not found. Run /ingest first.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/session/{repo_id}")
def clear_repo_session(repo_id: str) -> dict:
    """Clear the conversation history for a repository."""
    try:
        clear_session(repo_id)
        return {"status": "cleared"}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="repo_id not found. Run /ingest first.") from exc
