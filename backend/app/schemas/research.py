"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ── Request Schemas ───────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Generic error response."""
    detail: str
    error_code: str | None = None


class ResearchRequest(BaseModel):
    """Request body for submitting a new research task."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The research topic to investigate.",
        examples=["Latest methods for improving LLM reasoning"],
    )
    max_papers: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of papers to fetch and analyze.",
    )

    @field_validator("topic")
    @classmethod
    def sanitize_topic(cls, v: str) -> str:
        """Strip whitespace and basic sanitization."""
        v = v.strip()
        # Remove potential HTML/script tags
        import re
        v = re.sub(r"<[^>]*>", "", v)
        if len(v) < 3:
            raise ValueError("Topic must be at least 3 characters after sanitization.")
        return v


# ── Response Schemas ──────────────────────────────────────────────


class PaperSummary(BaseModel):
    """Summary of a single paper."""

    id: str
    title: str
    authors: str | None = None
    url: str
    source: str
    abstract: str | None = None
    summary: str | None = None
    relevance_score: float | None = None


class ResearchCreated(BaseModel):
    """Response after creating a research task."""

    task_id: str
    topic: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchStatus(BaseModel):
    """Current status of a research task."""

    task_id: str
    topic: str
    status: str
    progress: int = Field(ge=0, le=100)
    current_stage: str
    papers_found: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComparisonEntry(BaseModel):
    """A single row in the technique comparison table."""

    method: str
    description: str
    strengths: str
    limitations: str
    source: str


class ResearchReport(BaseModel):
    """Structured research report."""

    task_id: str
    topic: str
    summary: str
    key_techniques: list[str]
    comparison_table: list[ComparisonEntry]
    future_directions: list[str]
    references: list[str]
    papers: list[PaperSummary]
    generated_at: datetime


class ResearchHistoryItem(BaseModel):
    """Single item in research history list."""

    task_id: str
    topic: str
    status: str
    progress: int
    papers_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResearchHistoryResponse(BaseModel):
    """Paginated research history."""

    tasks: list[ResearchHistoryItem]
    total: int
    page: int
    page_size: int


class ChatRequest(BaseModel):
    """Request for chatting with a research task."""
    message: str = Field(..., min_length=1, max_length=1000)

class ChatResponse(BaseModel):
    """Response from chat with context."""
    answer: str
    sources: list[dict] = []
