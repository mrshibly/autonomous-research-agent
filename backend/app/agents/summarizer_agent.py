"""
Summarizer Agent — uses LLM to summarize research papers.
"""

from typing import Any

from loguru import logger

from app.agents.base import BaseAgent
from app.utils.llm_client import call_llm


class SummarizerAgent(BaseAgent):
    """Summarizes research papers using LLM."""

    @property
    def name(self) -> str:
        return "Summarizer Agent"

    @property
    def description(self) -> str:
        return "Generates concise summaries of research papers using LLM."

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Summarize each paper.

        Input:
            papers (list[dict]): Papers with full_text or abstract.
            topic (str): The original research topic.

        Output:
            papers (list[dict]): Papers with added summary field.
        """
        papers = input_data["papers"]
        topic = input_data["topic"]

        summarized_papers: list[dict] = []

        for paper in papers:
            text = paper.get("full_text") or paper.get("abstract", "")

            if not text or len(text.strip()) < 50:
                paper["summary"] = "Insufficient text available for summarization."
                summarized_papers.append(paper)
                continue

            # Truncate very long texts to avoid token limits
            max_chars = 12000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[Text truncated for summarization]"

            summary = await self._summarize_paper(
                title=paper.get("title", "Unknown"),
                text=text,
                topic=topic,
            )
            paper["summary"] = summary
            summarized_papers.append(paper)

        successful = sum(
            1 for p in summarized_papers
            if p.get("summary") and "Insufficient" not in p["summary"]
        )
        logger.info(f"Summarized {successful}/{len(papers)} papers.")

        return {"papers": summarized_papers}

    async def _summarize_paper(
        self, title: str, text: str, topic: str
    ) -> str:
        """Generate a summary for a single paper."""
        prompt = f"""Summarize the following research paper in the context of the topic: "{topic}"

Paper Title: {title}

Paper Text:
{text}

Provide a structured summary with:
1. **Main Contribution**: What is the key contribution of this paper? (2-3 sentences)
2. **Methodology**: What approach/method does it use? (2-3 sentences)
3. **Key Findings**: What are the main results? (2-3 bullet points)
4. **Relevance**: How does this relate to "{topic}"? (1-2 sentences)

Be concise and accurate. Only state what is explicitly in the paper."""

        try:
            summary = await call_llm(
                prompt=prompt,
                system_prompt=(
                    "You are an expert academic research summarizer. "
                    "Provide concise, accurate summaries. Never fabricate information."
                ),
                temperature=0.2,
                max_tokens=1024,
            )
            return summary

        except Exception as exc:
            logger.error(f"Summarization failed for '{title}': {exc}")
            return f"Summarization failed: {exc}"
