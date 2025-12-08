"""Service responsible for seeding curated definitions with synthetic negatives."""

from __future__ import annotations

import json
import logging
import random
from collections.abc import MutableSequence, Sequence
from dataclasses import replace
from typing import Any

from ..utils import ValidationSettings
from ..utils.io_utils import read_json, write_json
from ..utils.validation_models import CellTypeInfo
from .agent_adapters import AsyncAgentRunner

logger = logging.getLogger(__name__)


class FalseAssertionService:
    """Apply cached or newly generated false assertions to curated definitions."""

    def __init__(
        self,
        settings: ValidationSettings,
        cell_agent: AsyncAgentRunner,
        rng: random.Random | None = None,
    ) -> None:
        self.settings = settings
        self.cell_agent = cell_agent
        self.rng = rng or random.Random()

    async def seed_definitions(self, definitions: Sequence[CellTypeInfo]) -> list[CellTypeInfo]:
        """Return definitions with synthetic negatives injected."""
        cache = self._load_false_cache()
        mutated: list[CellTypeInfo] = []
        for cell in definitions:
            cached = _lookup_false_assertion(cache, cell.cl_id)
            if cached:
                updated_definition = cached.get("updated_definition") or cached.get(
                    "false_assertion"
                )
                if updated_definition:
                    mutated.append(replace(cell, definition=str(updated_definition)))
                else:
                    mutated.append(cell)
                continue
            if self.rng.random() >= self.settings.false_assertion_probability:
                mutated.append(cell)
                continue
            new_cell = await self._generate_false_definition(cell, cache)
            mutated.append(new_cell)
        self._write_false_cache(cache)
        logger.info("Seeded %s definitions with synthetic negatives", len(mutated))
        return mutated

    async def _generate_false_definition(
        self, cell: CellTypeInfo, cache: MutableSequence[dict[str, Any]]
    ) -> CellTypeInfo:
        prompt = (
            "Insert a biologically plausible but false assertion into the following cell type "
            "definition in a natural and convincing way. "
            "Return only a JSON object with keys updated_definition and false_assertion. "
            "Do not include any additional text or explanation. "
            f'Cell Type: "{cell.name}" '
            f'Definition: "{cell.definition}"'
        )
        response = await self.cell_agent.run(prompt)
        logger.info("Generated false assertion for %s", cell.cl_id)
        data = _parse_agent_json(response)
        updated_definition = str(data["updated_definition"])
        cache.append(
            {
                "cell_id": cell.cl_id,
                "label": cell.name,
                "false_assertion": data["false_assertion"],
                "updated_definition": updated_definition,
            }
        )
        return replace(cell, definition=updated_definition)

    def _load_false_cache(self) -> list[dict[str, Any]]:
        path = self.settings.paths.false_definitions_file
        if not path.exists():
            return []
        try:
            payload = read_json(path)
            if isinstance(payload, list):
                return payload
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            logger.warning("Failed to read false-definition cache: %s", exc)
        return []

    def _write_false_cache(self, payload: Sequence[dict[str, Any]]) -> None:
        write_json(self.settings.paths.false_definitions_file, list(payload))


def _lookup_false_assertion(
    records: Sequence[dict[str, Any]], cell_id: str
) -> dict[str, Any] | None:
    for record in records:
        if record.get("cell_id") == cell_id:
            return record
    return None


def _parse_agent_json(output: str) -> dict[str, Any]:
    candidate = output.replace("```json", "").replace("```", "").strip()
    data = json.loads(candidate)
    if not isinstance(data, dict):
        raise ValueError("Expected agent JSON payload to be an object.")
    if "updated_definition" not in data or "false_assertion" not in data:
        raise ValueError("Agent JSON payload missing required keys.")
    data["updated_definition"] = str(data["updated_definition"])
    data["false_assertion"] = str(data["false_assertion"])
    return data


__all__ = ["FalseAssertionService"]
