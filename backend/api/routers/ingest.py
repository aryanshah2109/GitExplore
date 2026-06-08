"""Ingestion router."""

from fastapi import APIRouter, HTTPException

from backend.api.schemas.ingest import IngestRequest, IngestResponse
from backend.api.services.ingest_service import run_ingestion

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest_repo(request: IngestRequest) -> IngestResponse:
    """Ingest a repository into the session store and vector index."""
    try:
        return run_ingestion(request.repo_url, request.branch)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
