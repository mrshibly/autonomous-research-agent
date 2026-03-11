"""
Base agent class — abstract interface for all AI agents.
"""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger


class BaseAgent(ABC):
    """
    Abstract base class for all research agents.

    Each agent has a name, description, and an async execute method
    that takes structured input and returns structured output.
    """

    def __init__(self) -> None:
        self._logger = logger.bind(agent=self.name)

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """What this agent does."""
        ...

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run the agent's main task.

        Args:
            input_data: Structured input specific to this agent.

        Returns:
            Structured output specific to this agent.
        """
        ...

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent with logging and error handling.

        This is the public entry point — wraps execute() with
        standardized logging, timing, and error handling.
        """
        self._logger.info(f"Starting {self.name}...")

        try:
            result = await self.execute(input_data)
            self._logger.info(f"{self.name} completed successfully.")
            return result

        except Exception as exc:
            self._logger.error(f"{self.name} failed: {exc}")
            return {
                "error": str(exc),
                "agent": self.name,
                "success": False,
            }
