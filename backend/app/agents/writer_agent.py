"""
Writer Agent — generates the final structured research report.
"""

import json
from typing import Any

from loguru import logger

from app.agents.base import BaseAgent
from app.utils.llm_client import call_llm


class WriterAgent(BaseAgent):
    """Compiles paper summaries into a final structured research report."""

    @property
    def name(self) -> str:
        return "Writer Agent"

    @property
    def description(self) -> str:
        return "Generates a comprehensive, structured research report from paper summaries."

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate or revise the final research report.

        Input:
            papers (list[dict]): Summarized and evaluated papers.
            topic (str): The original research topic.
            feedback (list[str], optional): Critique points from the Critic Agent.
            previous_report (dict, optional): The previous draft to improve.

        Output:
            report (dict): Structured report with all sections.
        """
        papers = input_data["papers"]
        topic = input_data["topic"]
        feedback = input_data.get("feedback")
        previous_report = input_data.get("previous_report")

        # Build paper summaries context for the LLM
        papers_context = self._build_papers_context(papers)

        # Generate or revise the report
        report = await self._generate_report(
            topic, papers_context, papers, feedback, previous_report
        )

        return {"report": report}

    def _build_papers_context(self, papers: list[dict]) -> str:
        """Build a formatted context string from all papers."""
        sections: list[str] = []

        for i, paper in enumerate(papers, 1):
            summary = paper.get("summary", "No summary available.")
            score = paper.get("relevance_score", 0)
            section = (
                f"--- Paper {i} ---\n"
                f"Title: {paper.get('title', 'Unknown')}\n"
                f"Authors: {paper.get('authors', 'Unknown')}\n"
                f"Source: {paper.get('url', 'N/A')}\n"
                f"Relevance Score: {score:.2f}\n"
                f"Summary:\n{summary}\n"
            )
            sections.append(section)

        return "\n".join(sections)

    async def _generate_report(
        self, 
        topic: str, 
        papers_context: str, 
        papers: list[dict],
        feedback: list[str] = None,
        previous_report: dict = None
    ) -> dict:
        """Generate or revise the structured report via LLM."""
        revision_context = ""
        if feedback and previous_report:
            import json
            revision_context = (
                f"\n\n--- PREVIOUS DRAFT ---\n{json.dumps(previous_report, indent=2)}\n\n"
                f"--- CRITIC FEEDBACK ---\n" + "\n".join([f"- {f}" for f in feedback]) + "\n\n"
                "Please REVISE the report to address the feedback above while maintaining the required JSON structure."
            )

        prompt = f"""Based on the following research papers, generate a comprehensive research report on the topic: "{topic}"

{papers_context}
{revision_context}

Generate a JSON report with EXACTLY this structure:
{{
    "summary": "A comprehensive 3-5 paragraph executive summary of the research findings",
    "key_techniques": ["technique1", "technique2", ...],
    "comparison_table": [
        {{
            "method": "Method Name",
            "description": "Brief description",
            "strengths": "Key strengths",
            "limitations": "Key limitations",
            "source": "Paper title or URL"
        }}
    ],
    "future_directions": ["direction1", "direction2", ...],
    "references": ["Full citation 1", "Full citation 2", ...]
}}

IMPORTANT:
- Synthesize findings across ALL papers.
- Address any Critic Feedback provided.
- Return ONLY valid JSON."""

        try:
            response = await call_llm(
                prompt=prompt,
                system_prompt=(
                    "You are an expert academic writer. Generate well-structured "
                    "research reports. Always return valid JSON. Never fabricate citations."
                ),
                temperature=0.3,
                max_tokens=4096,
            )

            # Parse the JSON response
            report = self._parse_report_json(response, topic, papers)
            return report

        except Exception as exc:
            logger.error(f"Report generation failed: {exc}")
            return self._fallback_report(topic, papers)

    def _parse_report_json(
        self, response: str, topic: str, papers: list[dict]
    ) -> dict:
        """Parse and validate the LLM's JSON response."""
        # Try to extract JSON from the response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])

        try:
            report = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON within the response
            import re
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                try:
                    report = json.loads(json_match.group())
                except json.JSONDecodeError:
                    return self._fallback_report(topic, papers)
            else:
                return self._fallback_report(topic, papers)

        # Ensure required fields
        report.setdefault("summary", "Report generation incomplete.")
        report.setdefault("key_techniques", [])
        report.setdefault("comparison_table", [])
        report.setdefault("future_directions", [])
        report.setdefault(
            "references",
            [f"{p.get('title', 'Unknown')} — {p.get('url', 'N/A')}" for p in papers],
        )

        return report

    def _fallback_report(self, topic: str, papers: list[dict]) -> dict:
        """Generate a basic report when LLM fails."""
        return {
            "summary": (
                f"Research on '{topic}' found {len(papers)} relevant papers. "
                "See individual paper summaries for details."
            ),
            "key_techniques": [
                p.get("title", "Unknown") for p in papers if p.get("title")
            ],
            "comparison_table": [],
            "future_directions": [
                "Further research needed to compare approaches in detail."
            ],
            "references": [
                f"{p.get('title', 'Unknown')} — {p.get('url', 'N/A')}"
                for p in papers
            ],
        }
