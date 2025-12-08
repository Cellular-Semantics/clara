"""Configuration helpers for the CL validation workflow."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CELL_DATA_DIR = "/Users/hk9/workspaces/workspace1/agentic-pipeline-testdata/data"
DEFAULT_TEST_TERMS = (
    "CL_4052001",
    "CL_4033092",
    "CL_4033088",
    "CL_4052055",
    "CL_4033094",
    "CL_4033084",
)
DEFAULT_FALSE_ASSERTION_PROBABILITY = 0.6


def _env_bool(env: Mapping[str, str], key: str, default: bool) -> bool:
    raw = env.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(env: Mapping[str, str], key: str, default: Sequence[str]) -> Sequence[str]:
    raw = env.get(key)
    if raw is None:
        return tuple(default)
    values = [entry.strip() for entry in raw.split(",") if entry.strip()]
    return tuple(values)


def _env_float(env: Mapping[str, str], key: str, default: float) -> float:
    raw = env.get(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Invalid float for {key}: {raw}") from exc


def _as_path(value: str | None, fallback: str) -> Path:
    path = Path(value or fallback).expanduser()
    return path


@dataclass
class ValidationPaths:
    """Filesystem layout for curated datasets, references, and caches."""

    cell_data_dir: Path
    dataset_file: Path
    references_dir: Path
    output_dir: Path
    false_definitions_file: Path
    paperqa_markdown_dir: Path
    paperqa_json_dir: Path

    def ensure_directories(self) -> None:
        """Create output and cache directories if they do not already exist."""
        for path in (self.output_dir, self.paperqa_markdown_dir, self.paperqa_json_dir):
            path.mkdir(parents=True, exist_ok=True)


@dataclass
class ValidationSettings:
    """Runtime configuration for the CL validation workflow."""

    paths: ValidationPaths
    is_test_mode: bool
    test_terms: Sequence[str]
    false_assertion_probability: float


def load_validation_settings(env: Mapping[str, str] | None = None) -> ValidationSettings:
    """Load workflow configuration, falling back to legacy defaults."""
    env = env or os.environ
    cell_data_dir = _as_path(env.get("CLARA_CELL_DATA_DIR"), DEFAULT_CELL_DATA_DIR)
    dataset_file = cell_data_dir / "cells_data.json"
    references_dir = cell_data_dir / "reference"
    output_dir = cell_data_dir / "output"
    false_definitions_file = output_dir / "cells_false_data.json"
    pqa_json_dir = output_dir / "pqa_jsons"

    paths = ValidationPaths(
        cell_data_dir=cell_data_dir,
        dataset_file=dataset_file,
        references_dir=references_dir,
        output_dir=output_dir,
        false_definitions_file=false_definitions_file,
        paperqa_markdown_dir=output_dir,
        paperqa_json_dir=pqa_json_dir,
    )

    is_test_mode = _env_bool(env, "CLARA_IS_TEST_MODE", False)
    test_terms = _env_list(env, "CLARA_TEST_TERMS", DEFAULT_TEST_TERMS)
    probability = _env_float(
        env,
        "CLARA_FALSE_ASSERTION_PROBABILITY",
        DEFAULT_FALSE_ASSERTION_PROBABILITY,
    )

    return ValidationSettings(
        paths=paths,
        is_test_mode=is_test_mode,
        test_terms=test_terms,
        false_assertion_probability=probability,
    )


__all__ = ["ValidationPaths", "ValidationSettings", "load_validation_settings"]
