"""Configuration for the CL validation cell agent."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CellValidationDependencies:
    """Runtime dependencies injected into the cell validation agent."""

    llm: str = field(
        default=os.environ.get("CLARA_CELL_AGENT_MODEL", "openai:gpt-4.1"),
        metadata={
            "description": (
                "LLM to use for generating and validating definitions. Default is openai:gpt-4.1."
            )
        },
    )
    temperature: float = field(
        default=float(os.environ.get("CLARA_CELL_AGENT_TEMPERATURE", 0.1)),
        metadata={"description": "Temperature for LLM responses. Default is 0.1."},
    )
    workdir: Path | None = field(
        default=None,
        metadata={"description": "Optional working directory for agent scratch files."},
    )

    def __post_init__(self) -> None:
        """Ensure the working directory exists when provided."""
        if self.workdir:
            self.workdir.mkdir(parents=True, exist_ok=True)


def get_cell_validation_config() -> CellValidationDependencies:
    """Load the cell agent configuration from the current environment."""
    workdir_path = os.environ.get("CLARA_WORKDIR")
    workdir = Path(workdir_path).expanduser() if workdir_path else None
    return CellValidationDependencies(workdir=workdir)


__all__ = ["CellValidationDependencies", "get_cell_validation_config"]
