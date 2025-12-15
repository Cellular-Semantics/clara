"""Legacy entrypoint preserved for backwards compatibility."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv

from clara.graphs import run_cl_validation_workflow

LOGGER_NAME = "clara.validation"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging() -> logging.Logger:
    """Mirror the legacy logging setup used by the archived script."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
    logger.propagate = False
    return logger


async def main() -> None:
    """Load environment configuration and run the refactored workflow."""
    configure_logging()
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    report_path = await run_cl_validation_workflow()
    logging.getLogger(LOGGER_NAME).info("Report generated at %s", report_path.resolve())


if __name__ == "__main__":
    asyncio.run(main())
