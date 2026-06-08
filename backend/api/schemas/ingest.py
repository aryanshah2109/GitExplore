"""Ingestion request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class IngestRequest(BaseModel):
    """Payload to ingest a repository."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_url: str = Field(..., min_length=1)
    branch: str = "main"


class IngestResponse(BaseModel):
    """Response after ingestion completes."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_id: str
    file_count: int
    chunk_count: int
    status: str

