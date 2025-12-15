"""Adapter interfaces for external agent clients used in the workflow."""

from __future__ import annotations

from typing import Protocol

from ..agents import CellValidationAgent, build_cell_validation_agent


class AsyncAgentRunner(Protocol):
    """Protocol for async agents returning textual outputs."""

    async def run(self, prompt: str) -> str:
        """Execute the given prompt and return the textual output."""


class CellAgentAdapter:
    """Adapter around the configured cell validation agent."""

    def __init__(self, agent: CellValidationAgent | None = None) -> None:
        self._agent = agent or build_cell_validation_agent()

    async def run(self, prompt: str) -> str:
        """Execute the prompt with the cell validation agent."""
        return await self._agent.run(prompt)


__all__ = ["AsyncAgentRunner", "CellAgentAdapter"]
