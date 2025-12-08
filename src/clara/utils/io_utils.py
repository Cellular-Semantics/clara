"""Shared IO helpers used across services and utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    """Load a JSON payload from disk."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    """Persist a JSON payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def read_text(path: Path) -> str:
    """Read text content from disk."""
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def write_text(path: Path, content: str) -> None:
    """Write text content to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content)


__all__ = ["read_json", "write_json", "read_text", "write_text"]
