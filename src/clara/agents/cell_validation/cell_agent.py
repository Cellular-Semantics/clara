"""Agent for validating and perturbing CL definitions."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .cell_agent_config import CellValidationDependencies, get_cell_validation_config
from .cell_agent_tools import read_json, read_text

cell_logger = logging.getLogger(__name__)
cell_logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
cell_logger.addHandler(console)
cell_logger.propagate = False

SYSTEM_PROMPT = """
You are a CL validation assistant. Your role is to inspect curated cell definitions,
inject plausible negative assertions when requested, and transform unstructured
reports into structured JSON data for downstream tooling.

Constraints:
- Use only the information provided in the prompt or referenced files/tools.
- Return data in the exact format requested (JSON objects or arrays).
- Avoid adding narrative prose outside of the requested structure.
"""


def _build_agent() -> Any:
    from pydantic_ai import Agent

    config = get_cell_validation_config()
    agent = Agent(
        model=config.llm,
        deps_type=CellValidationDependencies,
        output_type=str,
        system_prompt=SYSTEM_PROMPT,
        defer_model_check=True,
    )
    agent.tool(read_text)
    agent.tool(read_json)
    return agent


@dataclass
class CellValidationAgent:
    """Wrapper that lazily instantiates the underlying Pydantic AI agent."""

    agent: Any | None = field(default=None, init=False)

    async def run(self, prompt: str) -> str:
        """Execute the prompt and coerce the agent output to a string."""
        if self.agent is None:
            self.agent = _build_agent()
        result = await self.agent.run(prompt)
        return str(result.output)


def build_cell_validation_agent() -> CellValidationAgent:
    """Construct the default cell validation agent wrapper."""
    return CellValidationAgent()


__all__ = ["CellValidationAgent", "build_cell_validation_agent"]
