"""Load curated CL definitions from the shared dataset artifact."""

from __future__ import annotations

import logging

from ..utils import ValidationSettings
from ..utils.io_utils import read_json
from ..utils.validation_models import CellTypeInfo

logger = logging.getLogger(__name__)


class CellDatasetLoader:
    """Load and filter curated CL definitions for downstream validation."""

    def __init__(self, settings: ValidationSettings) -> None:
        self.settings = settings

    def load_definitions(self) -> list[CellTypeInfo]:
        """Load curated definitions from disk, applying reference/test filters."""
        payload = read_json(self.settings.paths.dataset_file)
        definitions: list[CellTypeInfo] = []
        total = 0
        selected_test_ids = set(self.settings.test_terms)
        for entry in payload.values():
            total += 1
            cell = CellTypeInfo.from_payload(entry)
            if self.settings.is_test_mode and cell.cl_id not in selected_test_ids:
                continue
            if not cell.has_all_references or not cell.references:
                continue
            definitions.append(cell)
        logger.info(
            "Loaded %s curated CL definitions (raw=%s test_mode=%s)",
            len(definitions),
            total,
            self.settings.is_test_mode,
        )
        return definitions


__all__ = ["CellDatasetLoader"]
