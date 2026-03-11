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
                # Use the abstract as a fallback summary if available
                abstract = paper.get("abstract", "")
                if abstract and len(abstract.strip()) >= 50:
                    paper["summary"] = abstract
                else:
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
        prompt = f"""Summarize the research paper: "{title}"
        
CONTEXT OF RESEARCH: "{topic}"

CONTENT TO SUMMARIZE:
{text}

Please provide a highly structured academic summary using exactly these sections:

### 1. Main Contribution
[2-3 sentences explaining the primary value or discovery]

### 2. Methodology
[2-3 sentences on the approach, datasets, or techniques used]

### 3. Key Findings
* [Bullet point 1]
* [Bullet point 2]
* [Bullet point 3 (if applicable)]

### 4. Relevance to "{topic}"
[1-2 sentences explaining why this paper is important for this specific topic]

Ensure the response is clean Markdown. Do not include page numbers, headers, or broken text artifacts."""

        try:
            summary = await call_llm(
                prompt=prompt,
                system_prompt=(
                    "You are an expert scientific researcher. Your task is to extract clear, "
                    "structured knowledge from papers. Avoid academic jargon where possible, "
                    "but stay technically accurate. Never mention PDF artifacts or software "
                    "extraction errors."
                ),
                temperature=0.1,
                max_tokens=1200,
            )
            return summary

        except Exception as exc:
            logger.error(f"Summarization failed for '{title}': {exc}")
            return f"Summarization failed: {exc}"
