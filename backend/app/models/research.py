"""
SQLAlchemy ORM models for research tasks and papers.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _generate_uuid() -> str:
    return uuid.uuid4().hex


class ResearchTask(Base):
    """A research task submitted by the user."""

    __tablename__ = "research_tasks"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[str] = mapped_column(String(50), default="queued")
    max_papers: Mapped[int] = mapped_column(Integer, default=5)

    # Final report stored as JSON
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    papers: Mapped[list["Paper"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ResearchTask id={self.id} topic='{self.topic[:30]}' status={self.status}>"


class Paper(Base):
    """A research paper discovered during a research task."""

    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid
    )
    task_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("research_tasks.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="arxiv")  # arxiv, web
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    task: Mapped["ResearchTask"] = relationship(back_populates="papers")

    def __repr__(self) -> str:
        return f"<Paper id={self.id} title='{self.title[:30]}'>"
