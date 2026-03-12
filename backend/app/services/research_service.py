"""
Research service — business logic for managing research tasks.
"""

import asyncio
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import init_db
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


async def _rebuild_vector_index(db: AsyncSession, task_id: str, vector_dir: str):
    """Rebuild the vector index from the database when files are missing."""
    from app.rag.vector_store import VectorStore
    from app.rag.chunker import chunk_text
    
    stmt = (
        select(ResearchTask)
        .where(ResearchTask.id == task_id)
        .options(selectinload(ResearchTask.papers))
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task or not task.papers:
        return None
    
    logger.info(f"Rebuilding vector index for task {task_id} from {len(task.papers)} papers")
    
    vector_store = VectorStore()
    all_chunks = []
    all_metadatas = []
    
    for paper in task.papers:
        text = paper.summary or paper.abstract or ""
        if text.strip():
            chunks = chunk_text(text, chunk_size=500, overlap=50)
            metadata = [{"paper_title": paper.title or "", "paper_url": paper.url or ""}] * len(chunks)
            all_chunks.extend(chunks)
            all_metadatas.extend(metadata)
    
    if not all_chunks:
        return None
    
    await vector_store.add_documents(all_chunks, all_metadatas)
    os.makedirs(vector_dir, exist_ok=True)
    vector_store.save(vector_dir)
    logger.info(f"Successfully rebuilt vector index at {vector_dir} with {len(all_chunks)} chunks")
    
    return vector_store


async def chat_with_task(
    db: AsyncSession, task_id: str, message: str
) -> ChatResponse:
    """Chat with the context of a specific research task."""
    stmt = select(ResearchTask).where(ResearchTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if task is None:
        raise ValueError(f"Research task {task_id} not found.")

    # Load VectorStore and HybridSearcher
    from app.rag.vector_store import VectorStore
    from app.rag.hybrid_search import HybridSearcher
    from app.utils.llm_client import call_llm
    
    # Use centralized absolute path from settings
    settings = get_settings()
    vector_dir = os.path.join(settings.data_dir, "vectors", task_id)
    
    # Check if data directory exists (system check)
    if not os.path.exists(settings.data_dir):
        os.makedirs(settings.data_dir, exist_ok=True)

    vector_store = None

    if os.path.exists(os.path.join(vector_dir, "index.faiss")):
        # Load existing vector store
        try:
            vector_store = VectorStore()
            vector_store.load(vector_dir)
            if not vector_store.documents:
                vector_store = None
        except Exception as e:
            logger.warning(f"Failed to load vector store from {vector_dir}: {e}")
            vector_store = None

    # If vector store is missing or empty, try to rebuild from DB
    if vector_store is None:
        if task.status != "completed":
            if task.progress < 50:
                raise RuntimeError(f"Still indexing research data ({task.progress}%). Please wait a moment.")
            raise RuntimeError("Research is still in progress. Please wait for it to complete.")
        
        logger.info(f"Vector index missing for completed task {task_id}. Attempting rebuild from database...")
        vector_store = await _rebuild_vector_index(db, task_id, vector_dir)
        
        if vector_store is None:
            raise RuntimeError(
                "Could not rebuild knowledge index. The research papers may not have been saved properly. "
                "Please start a new research task."
            )

    try:
        hybrid_searcher = HybridSearcher(vector_store)
        await hybrid_searcher.update_index(
            [d["text"] for d in vector_store.documents],
            [d["metadata"] for d in vector_store.documents]
        )

        # Retrieve context
        results = await hybrid_searcher.search(message, top_k=8)
        
        valid_results = [res for res in results if res.get("score", 1.0) >= 0.3]
        if not valid_results and results:
            valid_results = results[:3] 
            
        context_parts = []
        for res in valid_results:
            title = res['metadata'].get('paper_title', 'Unknown Paper')
            snippet = res['text']
            context_parts.append(f"--- PAPER: {title} ---\n{snippet}")
        
        context = "\n\n".join(context_parts)

        # Call LLM
        system_prompt = (
            f"You are a professional scientific research assistant specialized in '{task.topic}'.\n"
            "Answering based ONLY on the provided context.\n"
            "1. Cite the paper title.\n"
            "2. If unknown, say you don't have enough data from the papers.\n"
            "3. Be concise and technical."
        )
        user_prompt = f"CONTEXT:\n{context}\n\nUSER: {message}"
        
        try:
            answer = await call_llm(user_prompt, system_prompt)
        except Exception as llm_e:
            logger.error(f"LLM call failed: {str(llm_e)}")
            if "rate limit" in str(llm_e).lower() or "429" in str(llm_e):
                raise RuntimeError("AI model is currently rate-limited. Please try again in 1 minute.")
            raise RuntimeError(f"AI Service currently unavailable: {str(llm_e)}")

        return ChatResponse(
            answer=answer,
            sources=[res["metadata"] for res in results]
        )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Chat failed for task {task_id}: {str(e)}")
        raise RuntimeError(f"Chat processing error: {str(e)}")


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
