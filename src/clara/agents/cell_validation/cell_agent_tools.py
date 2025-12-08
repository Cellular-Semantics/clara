"""Utility tools available to the cell validation agent."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Generic, TypeVar

from .cell_agent_config import CellValidationDependencies

try:  # pragma: no cover - optional dependency
    from pydantic_ai import RunContext
except ImportError:  # pragma: no cover - define placeholder for type checking
    T = TypeVar("T")

    class RunContext(Generic[T]):  # type: ignore[no-redef]
        """Fallback RunContext used when pydantic_ai is unavailable."""

        ...


logger = logging.getLogger(__name__)


def read_text(ctx: RunContext[CellValidationDependencies], path: str) -> str:
    """Read a UTF-8 text file from disk."""
    file_path = Path(path).expanduser()
    logger.info("Reading text from %s", file_path)
    return file_path.read_text(encoding="utf-8")


def read_json(ctx: RunContext[CellValidationDependencies], path: str) -> Any:
    """Read a JSON payload from disk."""
    file_path = Path(path).expanduser()
    logger.info("Loading JSON from %s", file_path)
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


__all__ = ["read_text", "read_json"]
