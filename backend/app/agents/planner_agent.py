"""
Planner Agent — breaks down a research topic into multiple diverse search queries.
This ensures broader coverage across different aspects of the topic.
"""

from typing import Any
from loguru import logger
from app.agents.base import BaseAgent
from app.utils.llm_client import call_llm
import json
import re

class PlannerAgent(BaseAgent):
    """Generates a search plan with multiple targeted queries."""

    @property
    def name(self) -> str:
        return "Search Planner Agent"

    @property
    def description(self) -> str:
        return "Generates multiple diverse search queries for a research topic."

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate search queries.
        
        Input:
            topic (str): The main research topic.
            
        Output:
            queries (list[str]): A list of 3-5 search queries.
        """
        topic = input_data["topic"]
        
        system_prompt = (
            "You are a professional research planner. Your goal is to break down a single broad research topic "
            "into 3-5 specific, diverse search queries that cover different angles (e.g., technical, historical, "
            "comparative, application-based).\n\n"
            "Respond ONLY with a JSON list of strings."
        )
        
        user_prompt = f"Topic: {topic}\n\nQueries (JSON list):"
        
        try:
            response = await call_llm(system_prompt, user_prompt)
            
            # Extract JSON list
            match = re.search(r"(\[.*\])", response, re.DOTALL)
            if match:
                queries = json.loads(match.group(1))
            else:
                # Basic fallback if JSON parsing fails
                logger.warning(f"Failed to parse Planner JSON. Raw response: {response}")
                queries = [topic, f"{topic} latest methods", f"{topic} review paper"]

            # Validate and clean
            if not isinstance(queries, list):
                queries = [topic]
            
            queries = [q.strip() for q in queries if isinstance(q, str) and len(q) > 5]
            
            # Ensure at least the original topic is there if it's too short
            if not queries:
                queries = [topic]
                
            logger.info(f"Planner generated {len(queries)} queries for: {topic}")
            return {"queries": queries[:5]}

        except Exception as exc:
            logger.error(f"Planner Agent failed: {exc}")
            return {"queries": [topic]}
