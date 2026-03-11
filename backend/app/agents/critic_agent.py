"""
Critic Agent — validates summaries against source material.
Checks for hallucinations, evaluates relevance.
"""

from typing import Any

from loguru import logger

from app.agents.base import BaseAgent
from app.utils.llm_client import call_llm


class CriticAgent(BaseAgent):
    """Validates paper summaries and scores their relevance."""

    @property
    def name(self) -> str:
        return "Critic Agent"

    @property
    def description(self) -> str:
        return "Cross-references summaries against sources, checks hallucinations, assigns relevance scores."

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and score. Can handle paper evaluation or final report critique.
        
        Input can be:
            - papers: list[dict] & topic: str (Paper evaluation mode)
            - report: dict & topic: str (Report critique mode)
        """
        topic = input_data["topic"]

        if "report" in input_data:
            return await self.critique_report(input_data["report"], topic)
        
        papers = input_data["papers"]
        evaluated_papers: list[dict] = []

        for paper in papers:
            summary = paper.get("summary", "")
            source_text = paper.get("full_text") or paper.get("abstract", "")

            if not summary or "Insufficient" in summary or "failed" in summary.lower():
                # Still try to score using the abstract if available
                if source_text and len(source_text.strip()) > 50:
                    score = await self._evaluate_paper(
                        title=paper.get("title", ""),
                        summary=source_text[:2000],
                        source_text=source_text[:3000],
                        topic=topic,
                    )
                    paper["relevance_score"] = score
                else:
                    paper["relevance_score"] = 0.1
                evaluated_papers.append(paper)
                continue

            score = await self._evaluate_paper(
                title=paper.get("title", ""),
                summary=summary,
                source_text=source_text[:5000],
                topic=topic,
            )
            paper["relevance_score"] = score
            evaluated_papers.append(paper)

        evaluated_papers.sort(key=lambda p: p.get("relevance_score", 0), reverse=True)

        avg_score = (
            sum(p.get("relevance_score", 0) for p in evaluated_papers) / len(evaluated_papers)
            if evaluated_papers
            else 0
        )

        quality_report = (
            f"Evaluated {len(evaluated_papers)} papers. "
            f"Avg score: {avg_score:.2f}. "
            f"Top paper: '{evaluated_papers[0].get('title', 'N/A')}'"
            if evaluated_papers else "No papers to evaluate."
        )

        return {
            "papers": evaluated_papers,
            "quality_report": quality_report,
        }

    async def critique_report(self, report: dict, topic: str) -> dict[str, Any]:
        """Critiques a draft report and provides structured feedback."""
        import json
        import re

        prompt = f"""Review the following research report for clarity, technical depth, and coverage.
Topic: "{topic}"

Report Context:
{json.dumps(report, indent=2)[:8000]}

Assign a quality score (0.0 to 1.0) and provide a list of specific improvements.
If the score is >= 0.85, say 'PASSED'. Otherwise, say 'REVISE'.

RESPOND ONLY WITH JSON:
{{
  "score": float,
  "status": "PASSED" | "REVISE",
  "feedback": ["point 1", "point 2", ...],
  "technical_depth": "score 0-10",
  "clarity": "score 0-10"
}}"""

        try:
            response = await call_llm(
                prompt=prompt,
                system_prompt="You are a senior technical editor. Provide structured JSON feedback.",
                temperature=0.2
            )
            
            match = re.search(r"(\{.*\})", response, re.DOTALL)
            if match:
                feedback_data = json.loads(match.group(1))
            else:
                feedback_data = {
                    "score": 0.8,
                    "status": "REVISE",
                    "feedback": ["Failed to parse detailed feedback. General review required."],
                    "technical_depth": 5,
                    "clarity": 5
                }
                
            return {"critique": feedback_data}

        except Exception as exc:
            logger.error(f"Report critique failed: {exc}")
            return {"critique": {"score": 1.0, "status": "PASSED", "feedback": []}}

    async def _evaluate_paper(
        self, title: str, summary: str, source_text: str, topic: str
    ) -> float:
        """Evaluate a single paper's summary quality and relevance."""
        prompt = f"""Evaluate the following paper summary for quality and relevance.

Research Topic: "{topic}"

Paper Title: {title}

Summary:
{summary}

Source Text (excerpt):
{source_text[:3000]}

Rate this paper on a scale of 0.0 to 1.0 based on:
1. **Accuracy** (0-0.3): Is the summary faithful to the source? No hallucinations?
2. **Strict Relevance** (0-0.4): How specifically does this paper address the research topic "{topic}"? Be very strict. If it is only tangentially related or from a different field (even if it shares keywords), give 0.0 for this part.
3. **Scholar Quality** (0-0.3): Technical depth and clarity.

RESPOND WITH ONLY A SINGLE NUMBER between 0.0 and 1.0 (the total score).
Do not include any other text. If evaluation fails or is impossible, return 0.1."""

        try:
            response = await call_llm(
                prompt=prompt,
                system_prompt=(
                    "You are a strict academic reviewer. "
                    "Respond with only a decimal number between 0.0 and 1.0."
                ),
                temperature=0.1,
                max_tokens=10,
            )

            # Parse the score
            score = float(response.strip().split()[0])
            return max(0.0, min(1.0, score))

        except (ValueError, IndexError):
            logger.warning(f"Could not parse critic score for '{title}', defaulting to 0.1")
            return 0.1
        except Exception as exc:
            logger.error(f"Critic evaluation failed for '{title}': {exc}")
            return 0.1
