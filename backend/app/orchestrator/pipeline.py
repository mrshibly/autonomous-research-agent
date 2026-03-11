"""
Research pipeline orchestrator — coordinates all agents in sequence.
"""

from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.websocket_manager import manager
from app.agents.critic_agent import CriticAgent
from app.agents.paper_agent import PaperAgent
from app.agents.search_agent import SearchAgent
from app.agents.summarizer_agent import SummarizerAgent
from app.agents.writer_agent import WriterAgent
from app.models.research import Paper, ResearchTask
from app.rag.chunker import chunk_text
from app.rag.vector_store import VectorStore


class ResearchPipeline:
    """
    Orchestrates the multi-agent research pipeline.

    Pipeline stages:
    1. Search → Find relevant papers
    2. Paper  → Download & extract text
    3. RAG    → Chunk, embed, and store in vector DB
    4. Summarize → Summarize each paper via LLM
    5. Critic → Validate summaries and score relevance
    6. Writer → Generate the final structured report
    """

    STAGES = [
        ("searching", "Searching for papers...", 15),
        ("reading", "Downloading and reading papers...", 30),
        ("indexing", "Building knowledge base...", 45),
        ("summarizing", "Summarizing papers...", 60),
        ("evaluating", "Evaluating quality...", 75),
        ("writing", "Generating report...", 90),
        ("completed", "Research complete!", 100),
    ]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        from app.agents.planner_agent import PlannerAgent
        self.planner_agent = PlannerAgent()
        self.search_agent = SearchAgent()
        self.paper_agent = PaperAgent()
        self.summarizer_agent = SummarizerAgent()
        self.critic_agent = CriticAgent()
        self.writer_agent = WriterAgent()

    async def run(self, task: ResearchTask) -> None:
        """
        Run the full research pipeline with planning and self-correction.
        """
        try:
            topic = task.topic
            max_papers = task.max_papers

            # ── Stage 0: Planning ─────────────────────────────────
            await self._update_status(task, "planning", 5)
            plan_result = await self.planner_agent.run({"topic": topic})
            queries = plan_result.get("queries", [topic])
            
            # ── Stage 1: Multi-Query Search ────────────────────────
            await self._update_status(task, "searching", 10)

            all_papers = []
            seen_urls = set()
            
            # Use multi-queries to gather more diverse papers
            for i, query in enumerate(queries):
                logger.info(f"Query {i+1}/{len(queries)}: {query}")
                search_result = await self.search_agent.run({
                    "topic": query,
                    "max_results": max(2, max_papers // len(queries)),
                })
                
                for paper in search_result.get("papers", []):
                    if paper.get("url") not in seen_urls:
                        all_papers.append(paper)
                        seen_urls.add(paper.get("url"))
                
                if len(all_papers) >= max_papers:
                    break

            if not all_papers:
                await self._fail_task(task, "No papers found for this topic.")
                return

            await self._save_papers(task, all_papers)
            await self._update_status(task, "searching", 15)

            # ── Stage 2: Paper Reading ────────────────────────────
            await self._update_status(task, "reading", 25)
            paper_result = await self.paper_agent.run({"papers": all_papers})
            papers = paper_result.get("papers", all_papers)
            await self._update_status(task, "reading", 35)

            # ── Stage 3: RAG Indexing ─────────────────────────────
            await self._update_status(task, "indexing", 40)
            try:
                from app.rag.hybrid_search import HybridSearcher
                vector_store = VectorStore()
                hybrid_searcher = HybridSearcher(vector_store)
                
                all_chunks = []
                all_metadatas = []
                for paper in papers:
                    text = paper.get("full_text") or paper.get("abstract", "")
                    if text:
                        chunks = chunk_text(text)
                        metadata = [{"paper_title": paper.get("title", ""), "paper_url": paper.get("url", "")}] * len(chunks)
                        all_chunks.extend(chunks)
                        all_metadatas.extend(metadata)
                
                if all_chunks:
                    await vector_store.add_documents(all_chunks, all_metadatas)
                    await hybrid_searcher.update_index(all_chunks, all_metadatas)
                    vector_store.save(f"./data/vectors/{task.id}")
                    self.hybrid_searcher = hybrid_searcher
            except Exception as exc:
                logger.warning(f"RAG indexing failed: {exc}")

            await self._update_status(task, "indexing", 50)

            # ── Stage 4: Summarization ────────────────────────────
            await self._update_status(task, "summarizing", 55)
            summary_result = await self.summarizer_agent.run({"papers": papers, "topic": topic})
            papers = summary_result.get("papers", papers)
            await self._update_status(task, "summarizing", 65)

            # ── Stage 5: Critic Evaluation (Papers) ───────────────
            await self._update_status(task, "evaluating", 70)
            critic_result = await self.critic_agent.run({"papers": papers, "topic": topic})
            papers = critic_result.get("papers", papers)
            await self._update_status(task, "evaluating", 75)

            # ── Stage 6: Iterative Report Writing ─────────────────
            await self._update_status(task, "writing", 80)
            
            current_report = None
            feedback = None
            max_revisions = 2
            
            for attempt in range(max_revisions + 1):
                logger.info(f"Report writing attempt {attempt + 1}")
                writer_result = await self.writer_agent.run({
                    "papers": papers,
                    "topic": topic,
                    "feedback": feedback,
                    "previous_report": current_report
                })
                current_report = writer_result.get("report", {})
                
                # Critique the report
                critique_result = await self.critic_agent.run({
                    "report": current_report,
                    "topic": topic
                })
                critique = critique_result.get("critique", {})
                
                if critique.get("status") == "PASSED" or attempt == max_revisions:
                    logger.info(f"Report passed critic with score {critique.get('score')}")
                    break
                
                feedback = critique.get("feedback", [])
                logger.info(f"Report revision requested. Score: {critique.get('score')}")
                await self._update_status(task, "writing", 80 + (attempt + 1) * 5)

            # ── Complete ──────────────────────────────────────────
            task.report = current_report
            task.status = "completed"
            task.progress = 100
            task.current_stage = "completed"
            task.updated_at = datetime.now(timezone.utc)
            await self._update_papers(task, papers)
            await self.db.commit()
            logger.info(f"Research task {task.id} completed successfully.")

        except Exception as exc:
            logger.error(f"Pipeline failed for task {task.id}: {exc}")
            await self._fail_task(task, str(exc))

    async def _update_status(
        self, task: ResearchTask, stage: str, progress: int
    ) -> None:
        """Update task status in the database and broadcast via WebSocket."""
        task.status = stage
        task.current_stage = stage
        task.progress = progress
        task.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        # Broadcast update
        await manager.broadcast_update(str(task.id), {
            "status": stage,
            "current_stage": stage,
            "progress": progress,
            "topic": task.topic
        })
        
        logger.info(f"Task {task.id}: {stage} ({progress}%)")

    async def _fail_task(self, task: ResearchTask, error: str) -> None:
        """Mark a task as failed and broadcast via WebSocket."""
        task.status = "failed"
        task.error_message = error
        task.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        # Broadcast failure
        await manager.broadcast_update(str(task.id), {
            "status": "failed",
            "error_message": error,
            "progress": task.progress
        })
        
        logger.error(f"Task {task.id} failed: {error}")

    async def _save_papers(
        self, task: ResearchTask, papers: list[dict]
    ) -> None:
        """Save discovered papers to the database."""
        for paper_data in papers:
            paper = Paper(
                task_id=task.id,
                title=paper_data.get("title", "Unknown"),
                authors=paper_data.get("authors"),
                url=paper_data.get("url", ""),
                source=paper_data.get("source", "web"),
                abstract=paper_data.get("abstract"),
            )
            self.db.add(paper)
        await self.db.commit()

    async def _update_papers(
        self, task: ResearchTask, papers: list[dict]
    ) -> None:
        """Update paper records with summaries and scores."""
        from sqlalchemy import select

        stmt = select(Paper).where(Paper.task_id == task.id)
        result = await self.db.execute(stmt)
        db_papers = result.scalars().all()

        # Match by title
        paper_map = {p.get("title", ""): p for p in papers}
        for db_paper in db_papers:
            if db_paper.title in paper_map:
                data = paper_map[db_paper.title]
                db_paper.summary = data.get("summary")
                db_paper.relevance_score = data.get("relevance_score")
                db_paper.full_text = data.get("full_text")

        await self.db.commit()
