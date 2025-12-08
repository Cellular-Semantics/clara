"""Configuration helpers for the PaperQA agent used in CL validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PaperQADependencies:
    """Runtime configuration and dependencies for the PaperQA agent."""

    llm: str = field(
        default=os.environ.get("CLARA_PAPERQA_MODEL", "openai:gpt-4.1"),
        metadata={
            "description": (
                "LLM to use for extracting structured assertions from PaperQA prompts. "
                "Default is openai:gpt-4.1."
            )
        },
    )
    temperature: float = field(
        default=float(os.environ.get("CLARA_PAPERQA_TEMPERATURE", 0.0)),
        metadata={"description": "Temperature applied to PaperQA prompts."},
    )
    workdir: Path | None = field(
        default=None,
        metadata={"description": "Optional working directory for PaperQA scratch artifacts."},
    )

    def __post_init__(self) -> None:
        if self.workdir:
            self.workdir.mkdir(parents=True, exist_ok=True)


def get_paperqa_config() -> PaperQADependencies:
    """Return a PaperQA configuration sourced from environment variables."""
    workdir_path = os.environ.get("CLARA_PAPERQA_WORKDIR")
    workdir = Path(workdir_path).expanduser() if workdir_path else None
    return PaperQADependencies(workdir=workdir)


__all__ = ["PaperQADependencies", "get_paperqa_config"]
