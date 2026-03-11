"""
Search Agent — searches the web and Arxiv for research papers.
Uses DuckDuckGo (free, default) or SerpAPI.
"""

from typing import Any

from loguru import logger

from app.agents.base import BaseAgent
from app.config import get_settings


class SearchAgent(BaseAgent):
    """Searches the internet and Arxiv for relevant research papers."""

    @property
    def name(self) -> str:
        return "Search Agent"

    @property
    def description(self) -> str:
        return "Searches the web and Arxiv for research papers on a given topic."

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Search for papers related to the topic.

        Input:
            topic (str): The research topic.
            max_results (int): Maximum papers to find.

        Output:
            papers (list): List of paper dicts with title, url, abstract, source.
        """
        topic = input_data["topic"]
        max_results = input_data.get("max_results", 5)

        papers: list[dict] = []

        # 1. Search Arxiv (always free)
        arxiv_papers = await self._search_arxiv(topic, max_results)
        papers.extend(arxiv_papers)

        # 2. Search PubMed (always free)
        pubmed_papers = await self._search_pubmed(topic, max_results)
        papers.extend(pubmed_papers)

        # 3. Search web for additional papers
        settings = get_settings()
        if settings.search_provider == "duckduckgo":
            web_papers = await self._search_duckduckgo(topic, max_results)
        elif settings.search_provider == "serpapi":
            web_papers = await self._search_serpapi(topic, max_results)
        else:
            web_papers = []

        papers.extend(web_papers)

        # Deduplicate by URL
        seen_urls: set[str] = set()
        unique_papers: list[dict] = []
        for paper in papers:
            if paper["url"] not in seen_urls:
                seen_urls.add(paper["url"])
                unique_papers.append(paper)

        # Limit to max_results
        unique_papers = unique_papers[:max_results]

        logger.info(f"Found {len(unique_papers)} unique papers for topic: {topic}")

        return {"papers": unique_papers, "total_found": len(unique_papers)}

    async def _search_arxiv(
        self, topic: str, max_results: int
    ) -> list[dict]:
        """Search Arxiv API for papers."""
        try:
            import arxiv

            client = arxiv.Client()
            search = arxiv.Search(
                query=topic,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )

            papers = []
            for result in client.results(search):
                papers.append({
                    "title": result.title,
                    "authors": ", ".join(a.name for a in result.authors),
                    "url": result.pdf_url or result.entry_id,
                    "abstract": result.summary,
                    "source": "arxiv",
                    "published": str(result.published.date()) if result.published else None,
                })

            logger.info(f"Arxiv returned {len(papers)} papers.")
            return papers

        except Exception as exc:
            logger.warning(f"Arxiv search failed: {exc}")
            return []

    async def _search_duckduckgo(
        self, topic: str, max_results: int
    ) -> list[dict]:
        """Search DuckDuckGo for research papers (free, no API key)."""
        try:
            from duckduckgo_search import DDGS

            query = f"{topic} research paper site:arxiv.org OR site:scholar.google.com"
            papers = []

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            for r in results:
                papers.append({
                    "title": r.get("title", "Untitled"),
                    "authors": None,
                    "url": r.get("href", ""),
                    "abstract": r.get("body", ""),
                    "source": "web",
                })

            logger.info(f"DuckDuckGo returned {len(papers)} results.")
            return papers

        except Exception as exc:
            logger.warning(f"DuckDuckGo search failed: {exc}")
            return []

    async def _search_serpapi(
        self, topic: str, max_results: int
    ) -> list[dict]:
        """Search using SerpAPI (requires API key)."""
        try:
            import httpx

            settings = get_settings()
            if not settings.serpapi_key:
                logger.warning("SerpAPI key not configured, skipping.")
                return []

            params = {
                "q": f"{topic} research paper",
                "api_key": settings.serpapi_key,
                "engine": "google_scholar",
                "num": max_results,
            }

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://serpapi.com/search", params=params, timeout=30
                )
                resp.raise_for_status()
                data = resp.json()

            papers = []
            for r in data.get("organic_results", []):
                papers.append({
                    "title": r.get("title", "Untitled"),
                    "authors": r.get("publication_info", {}).get("authors", None),
                    "url": r.get("link", ""),
                    "abstract": r.get("snippet", ""),
                    "source": "serpapi",
                })

            logger.info(f"SerpAPI returned {len(papers)} results.")
            return papers

        except Exception as exc:
            logger.warning(f"SerpAPI search failed: {exc}")
            return []

    async def _search_pubmed(
        self, topic: str, max_results: int
    ) -> list[dict]:
        """Search PubMed via Entrez API."""
        try:
            from Bio import Entrez

            settings = get_settings()
            Entrez.email = settings.pubmed_email

            # 1. Search for IDs
            handle = Entrez.esearch(db="pubmed", term=topic, retmax=max_results)
            record = Entrez.read(handle)
            handle.close()
            id_list = record["IdList"]

            if not id_list:
                return []

            # 2. Fetch details (summaries)
            handle = Entrez.esummary(db="pubmed", id=",".join(id_list))
            records = Entrez.read(handle)
            handle.close()

            papers = []
            for r in records:
                papers.append({
                    "title": r.get("Title", "Untitled"),
                    "authors": ", ".join(r.get("AuthorList", [])),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{r.get('Id', '')}/",
                    "abstract": r.get("FullJournalName", ""), 
                    "source": "pubmed",
                })

            logger.info(f"PubMed returned {len(papers)} papers.")
            return papers

        except Exception as exc:
            logger.warning(f"PubMed search failed: {exc}")
            return []
