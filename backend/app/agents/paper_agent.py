"""
Paper Agent — downloads and extracts text from research papers / PDFs.
"""

from typing import Any

import httpx
from loguru import logger

from app.agents.base import BaseAgent
from app.utils.pdf_parser import extract_text_from_pdf


class PaperAgent(BaseAgent):
    """Downloads research papers and extracts their text content."""

    @property
    def name(self) -> str:
        return "Paper Agent"

    @property
    def description(self) -> str:
        return "Downloads PDFs from URLs and extracts text content."

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Download and extract text from papers.

        Input:
            papers (list[dict]): Papers with url, title, etc.

        Output:
            papers (list[dict]): Same papers with added full_text field.
        """
        papers = input_data["papers"]
        processed_papers: list[dict] = []

        async with httpx.AsyncClient(
            timeout=60,
            follow_redirects=True,
            headers={
                "User-Agent": "ResearchAgent/1.0 (Academic Research Tool)"
            },
        ) as client:
            for paper in papers:
                result = await self._process_paper(client, paper)
                processed_papers.append(result)

        successful = sum(1 for p in processed_papers if p.get("full_text"))
        logger.info(
            f"Paper Agent processed {len(processed_papers)} papers, "
            f"{successful} with text extracted."
        )

        return {"papers": processed_papers}

    async def _process_paper(
        self, client: httpx.AsyncClient, paper: dict
    ) -> dict:
        """Download and extract text from a single paper."""
        url = paper.get("url", "")
        paper_result = {**paper}

        if not url:
            paper_result["full_text"] = None
            paper_result["extraction_error"] = "No URL provided"
            return paper_result

        # Check if URL points to a PDF
        is_pdf_url = url.endswith(".pdf") or "/pdf/" in url

        if is_pdf_url:
            text = await self._download_and_extract_pdf(client, url)
            paper_result["full_text"] = text
        else:
            # Try fetching as PDF first, then fall back to abstract
            text = await self._download_and_extract_pdf(client, url)
            if text:
                paper_result["full_text"] = text
            else:
                # Use abstract as fallback
                paper_result["full_text"] = paper.get("abstract", "")
                logger.info(
                    f"Using abstract as fallback for: {paper.get('title', 'Unknown')}"
                )

        return paper_result

    async def _download_and_extract_pdf(
        self, client: httpx.AsyncClient, url: str
    ) -> str | None:
        """Download a PDF and extract its text."""
        try:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            if "application/pdf" in content_type or url.endswith(".pdf"):
                text = extract_text_from_pdf(response.content)
                if text and len(text) > 100:
                    logger.info(f"Extracted {len(text)} chars from PDF: {url[:80]}")
                    return text

            return None

        except Exception as exc:
            logger.warning(f"PDF download/extraction failed for {url[:80]}: {exc}")
            return None
