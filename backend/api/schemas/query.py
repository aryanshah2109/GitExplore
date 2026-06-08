"""Query request and response schemas."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class JudgementSchema(BaseModel):
    """Scores returned by the judge model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    faithfulness: int
    retrieval_relevance: int
    citation_accuracy: int
    query_type_fit: int
    reasoning: str


class QueryRequest(BaseModel):
    """Payload for asking a question about a repository."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)


class QueryResponse(BaseModel):
    """Response returned by the query endpoint."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    answer: str
    query_type: str
    judgement: JudgementSchema
    citation_validation: Dict[str, Any]
    status: str

