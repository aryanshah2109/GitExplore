from git.exc import GitCommandError
from fastapi import APIRouter, HTTPException

from backend.api.schemas.ingest import IngestRequest, IngestResponse
from backend.api.services.ingest_service import run_ingestion

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest_repo(request: IngestRequest) -> IngestResponse:
    try:
        return run_ingestion(request.repo_url, request.branch)

    except GitCommandError as exc:
        error_text = str(exc)

        if "Remote branch" in error_text and "not found" in error_text:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Branch '{request.branch}' was not found in the repository. "
                    f"Try using 'main' or check the repository branches."
                ),
            )

        raise HTTPException(
            status_code=400,
            detail="Failed to clone repository.",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(exc)}",
        )