"""Service orchestrating PaperQA assertion extraction."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from ..agents import PaperQAAgent, build_paperqa_agent
from ..utils import ValidationSettings
from ..utils.io_utils import read_text, write_text
from ..utils.validation_models import CellTypeInfo, PaperQAResult

logger = logging.getLogger(__name__)


class PaperQAService:
    """Run PaperQA via the configured agent and cache markdown outputs per cell type."""

    def __init__(
        self,
        settings: ValidationSettings,
        agent: PaperQAAgent | None = None,
    ) -> None:
        self.settings = settings
        self._agent = agent or build_paperqa_agent()

    async def validate_cells(self, cells: Iterable[CellTypeInfo]) -> list[PaperQAResult]:
        """Run PaperQA for each cell, caching markdown outputs."""
        results: list[PaperQAResult] = []
        for cell in cells:
            markdown_path = self._markdown_path(cell.cl_id)
            if markdown_path.exists():
                markdown = read_text(markdown_path)
            else:
                markdown = await self._ask_assertions(cell)
                write_text(markdown_path, markdown)
            results.append(PaperQAResult(cell_type=cell, report_markdown=markdown))
        logger.info("PaperQA processed %s cells", len(results))
        return results

    def _markdown_path(self, cell_id: str) -> Path:
        return self.settings.paths.paperqa_markdown_dir / f"{cell_id}.md"

    async def _ask_assertions(self, cell: CellTypeInfo) -> str:
        prompt = self._build_prompt(cell)
        return await self._agent.run(prompt)

    @staticmethod
    def _build_prompt(cell: CellTypeInfo) -> str:
        logical_assertions = "\n".join(
            part.strip() for part in cell.logical_axioms.split(".") if part.strip()
        )
        return (
            "For the following text, first break down the definition into individual, atomic "
            "assertions. Each assertion should be a single, verifiable statement. After extracting "
            "the assertions, create a table with the following columns:\n"
            "- Assertion: A single, verifiable statement about the cell type.\n"
            '- Validated: A strict "True" or "False" value. This column should only contain "True" '
            "if the entire assertion is stated and supported by the provided literature. If the "
            "literature contradicts the assertion, or is not supported, the value must be False.\n"
            "- Evidence: A brief summary of the evidence from the literature that supports the "
            '"Validated" column\'s value.\n'
            "- References: The sources from the literature that were used for validation.\n\n"
            f"name: {cell.name}\n"
            f'def: "{cell.definition}"\n'
            f"{logical_assertions}"
        )


__all__ = ["PaperQAService"]
