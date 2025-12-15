#!/usr/bin/env python
"""CLI entrypoint for the CL validation workflow."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

from clara import bootstrap
from clara.graphs import run_cl_validation_workflow
from clara.utils import ValidationPaths, ValidationSettings, load_validation_settings


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for the CL validation workflow."""
    parser = argparse.ArgumentParser(
        description="Run the CL validation workflow against curated datasets."
    )
    parser.add_argument(
        "--cell-data-dir",
        type=Path,
        help="Override the base cell data directory (defaults to CLARA_CELL_DATA_DIR).",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Enable test mode to restrict processing to test terms.",
    )
    parser.add_argument(
        "--test-term",
        dest="test_terms",
        action="append",
        help="Specific CL IDs to process when test mode is enabled (repeatable).",
    )
    parser.add_argument(
        "--false-assertion-probability",
        type=float,
        help="Probability of injecting a synthetic false assertion (default inherited).",
    )
    parser.add_argument(
        "--dotenv",
        type=Path,
        help="Optional path to a .env file that should be loaded before execution.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity.",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    """Configure root logging for the CLI."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _apply_overrides(settings: ValidationSettings, args: argparse.Namespace) -> ValidationSettings:
    if args.cell_data_dir:
        base = args.cell_data_dir.expanduser().resolve()
        output_dir = base / "output"
        paths = ValidationPaths(
            cell_data_dir=base,
            dataset_file=base / "cells_data.json",
            references_dir=base / "reference",
            output_dir=output_dir,
            false_definitions_file=output_dir / "cells_false_data.json",
            paperqa_markdown_dir=output_dir,
            paperqa_json_dir=output_dir / "pqa_jsons",
        )
        settings.paths = paths
    if args.test_mode:
        settings.is_test_mode = True
    if args.test_terms:
        settings.test_terms = tuple(args.test_terms)
    if args.false_assertion_probability is not None:
        settings.false_assertion_probability = float(args.false_assertion_probability)
    return settings


async def _async_main(args: argparse.Namespace) -> None:
    """Async entrypoint wiring CLI args into the workflow."""
    bootstrap(str(args.dotenv) if args.dotenv else None)
    settings = load_validation_settings()
    settings = _apply_overrides(settings, args)
    report_path = await run_cl_validation_workflow(settings=settings)
    logging.getLogger("clara.validation").info("Report generated at %s", report_path)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entrypoint that executes the CL validation workflow."""
    args = parse_args(argv)
    configure_logging(args.log_level)
    try:
        asyncio.run(_async_main(args))
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
