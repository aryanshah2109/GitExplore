"""Health check router."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Return a simple health payload."""
    return {"status": "ok", "service": "GitExplore"}
