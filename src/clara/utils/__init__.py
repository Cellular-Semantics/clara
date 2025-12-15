"""Repo-specific utilities that do not belong in agents/services."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .cl_validation_config import (
    ValidationPaths,
    ValidationSettings,
    load_validation_settings,
)
from .io_utils import read_json, read_text, write_json, write_text
from .validation_models import CellTypeInfo, PaperQAResult, ValidationState


def chunk_items(items: Iterable[str], size: int = 10) -> list[list[str]]:
    """Simple batching helper for splitting sequences in tooling scripts."""
    batch: list[str] = []
    result: list[list[str]] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            result.append(batch)
            batch = []
    if batch:
        result.append(batch)
    return result


@dataclass
class ToolingContext:
    """Context object that CLI scripts can extend with repo-specific settings."""

    workspace: str
    dry_run: bool = False


__all__ = [
    "chunk_items",
    "ToolingContext",
    "ValidationPaths",
    "ValidationSettings",
    "load_validation_settings",
    "CellTypeInfo",
    "PaperQAResult",
    "ValidationState",
    "read_json",
    "write_json",
    "read_text",
    "write_text",
]
