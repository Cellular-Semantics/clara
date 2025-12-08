"""Agent for extracting structured assertions from PaperQA outputs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .paperqa_config import PaperQADependencies, get_paperqa_config

paperqa_logger = logging.getLogger(__name__)
paperqa_logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
paperqa_logger.addHandler(console)
paperqa_logger.propagate = False

SYSTEM_PROMPT = """
You are a PaperQA summarization assistant. Extract atomic assertions from the
provided markdown or free-form text, normalize them into JSON structures, and
ensure each entry includes assertion text, validation flag, summary/evidence,
and reference citations. Never include narrative text outside the JSON payload.
"""


def _build_agent() -> Any:
    from pydantic_ai import Agent

    config = get_paperqa_config()
    agent = Agent(
        model=config.llm,
        deps_type=PaperQADependencies,
        output_type=str,
        system_prompt=SYSTEM_PROMPT,
        defer_model_check=True,
    )
    return agent


@dataclass
class PaperQAAgent:
    """Wrapper exposing a stable async interface to the PaperQA agent."""

    agent: Any | None = field(default=None, init=False)

    async def run(self, prompt: str) -> str:
        """Execute the prompt and coerce the agent output to a string."""
        if self.agent is None:
            self.agent = _build_agent()
        result = await self.agent.run(prompt)
        return str(result.output)


def build_paperqa_agent() -> PaperQAAgent:
    """Construct the default PaperQA agent wrapper."""
    return PaperQAAgent()


__all__ = ["PaperQAAgent", "build_paperqa_agent"]
