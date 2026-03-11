"""
Research service — business logic for managing research tasks.
"""

import asyncio
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models.research import Paper, ResearchTask
from app.orchestrator.pipeline import ResearchPipeline
from app.schemas.research import (
    ComparisonEntry,
    PaperSummary,
    ResearchCreated,
    ResearchHistoryItem,
    ResearchHistoryResponse,
    ResearchReport,
    ResearchStatus,
    ChatResponse,
)
import os


async def create_research_task(
    db: AsyncSession, topic: str, max_papers: int = 5
) -> ResearchCreated:
    """
    Create a new research task and launch the pipeline in the background.

    Args:
        db: Database session.
        topic: Research topic.
        max_papers: Maximum papers to fetch.

    Returns:
        ResearchCreated response with task ID.
    """
    task = ResearchTask(
        topic=topic,
        max_papers=max_papers,
        status="pending",
        progress=0,
        current_stage="queued",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    logger.info(f"Created research task {task.id}: '{topic}'")

    # Launch the pipeline in the background
    asyncio.create_task(_run_pipeline_background(task.id))

    return ResearchCreated(
        task_id=task.id,
        topic=task.topic,
        status=task.status,
        created_at=task.created_at,
    )


async def _run_pipeline_background(task_id: str) -> None:
    """Run the research pipeline in a background task."""
    async with async_session() as db:
        try:
            stmt = select(ResearchTask).where(ResearchTask.id == task_id)
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if task is None:
                logger.error(f"Task {task_id} not found for background processing.")
                return

            pipeline = ResearchPipeline(db)
            await pipeline.run(task)

        except Exception as exc:
            logger.error(f"Background pipeline failed for task {task_id}: {exc}")
            try:
                task.status = "failed"
                task.error_message = str(exc)
                await db.commit()
            except Exception:
                pass


async def get_task_status(db: AsyncSession, task_id: str) -> ResearchStatus | None:
    """Get the current status of a research task."""
    stmt = (
        select(ResearchTask)
        .where(ResearchTask.id == task_id)
        .options(selectinload(ResearchTask.papers))
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if task is None:
        return None

    return ResearchStatus(
        task_id=task.id,
        topic=task.topic,
        status=task.status,
        progress=task.progress,
        current_stage=task.current_stage,
        papers_found=len(task.papers),
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


async def get_report(db: AsyncSession, task_id: str) -> ResearchReport | None:
    """Get the completed research report for a task."""
    stmt = (
        select(ResearchTask)
        .where(ResearchTask.id == task_id)
        .options(selectinload(ResearchTask.papers))
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if task is None or task.status != "completed" or task.report is None:
        return None

    report_data = task.report

    # Build paper summaries
    papers = [
        PaperSummary(
            id=p.id,
            title=p.title,
            authors=p.authors,
            url=p.url,
            source=p.source,
            abstract=p.abstract,
            summary=p.summary,
            relevance_score=p.relevance_score,
        )
        for p in task.papers
    ]

    # Parse comparison table
    comparison_table = []
    for entry in report_data.get("comparison_table", []):
        if isinstance(entry, dict):
            comparison_table.append(
                ComparisonEntry(
                    method=entry.get("method", ""),
                    description=entry.get("description", ""),
                    strengths=entry.get("strengths", ""),
                    limitations=entry.get("limitations", ""),
                    source=entry.get("source", ""),
                )
            )

    return ResearchReport(
        task_id=task.id,
        topic=task.topic,
        summary=report_data.get("summary", ""),
        key_techniques=report_data.get("key_techniques", []),
        comparison_table=comparison_table,
        future_directions=report_data.get("future_directions", []),
        references=report_data.get("references", []),
        papers=papers,
        generated_at=task.updated_at,
    )


async def get_history(
    db: AsyncSession, page: int = 1, page_size: int = 20
) -> ResearchHistoryResponse:
    """Get paginated research task history."""
    # Count total
    count_stmt = select(func.count()).select_from(ResearchTask)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Fetch page
    offset = (page - 1) * page_size
    stmt = (
        select(ResearchTask)
        .options(selectinload(ResearchTask.papers))
        .order_by(ResearchTask.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    items = [
        ResearchHistoryItem(
            task_id=t.id,
            topic=t.topic,
            status=t.status,
            progress=t.progress,
            papers_count=len(t.papers),
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tasks
    ]

    return ResearchHistoryResponse(
        tasks=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def chat_with_task(
    db: AsyncSession, task_id: str, message: str
) -> ChatResponse | None:
    """Chat with the context of a specific research task."""
    stmt = select(ResearchTask).where(ResearchTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if task is None or task.status != "completed":
        return None

    # Load VectorStore and HybridSearcher
    from app.rag.vector_store import VectorStore
    from app.rag.hybrid_search import HybridSearcher
    from app.utils.llm_client import call_llm
    
    vector_dir = f"./data/vectors/{task_id}"
    if not os.path.exists(vector_dir):
        logger.warning(f"Vector index not found for task {task_id}")
        return None

    vector_store = VectorStore()
    vector_store.load(vector_dir)
    hybrid_searcher = HybridSearcher(vector_store)
    await hybrid_searcher.update_index(
        [d["text"] for d in vector_store.documents],
        [d["metadata"] for d in vector_store.documents]
    )

    # Retrieve context
    results = await hybrid_searcher.search(message, top_k=5)
    context = "\n\n".join([f"Source: {res['metadata'].get('paper_title')}\nContent: {res['content']}" for res in results])

    # Call LLM
    system_prompt = (
        f"You are a scientific research assistant. You are helping a user explore a research report on '{task.topic}'.\n"
        "Use the provided context from research papers to answer the user's question.\n"
        "If you don't know the answer, say so. Be concise and technical."
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {message}"
    
    answer = await call_llm(system_prompt, user_prompt)

    return ChatResponse(
        answer=answer,
        sources=[res["metadata"] for res in results]
    )


async def delete_task(db: AsyncSession, task_id: str) -> bool:
    """Delete a research task and its associated papers."""
    stmt = select(ResearchTask).where(ResearchTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if task is None:
        return False

    await db.delete(task)
    await db.commit()

    logger.info(f"Deleted research task {task_id}")
    return True
