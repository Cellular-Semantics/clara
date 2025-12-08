"""Service responsible for building curator-ready TSV reports."""

from __future__ import annotations

import csv
import json
import logging
from collections.abc import Iterable
from pathlib import Path

from ..utils import ValidationSettings
from ..utils.io_utils import read_json, write_json
from ..utils.validation_models import PaperQAResult
from .agent_adapters import AsyncAgentRunner

logger = logging.getLogger(__name__)

COLUMN_NAMES = [
    "Cell ID",
    "Name",
    "Assertion",
    "Agent Validation",
    "Curator Validation",
    "References",
    "Curator Notes",
    "Agent Notes",
]


class ReportBuilder:
    """Build unified TSV reports derived from cached PaperQA outputs."""

    def __init__(self, settings: ValidationSettings, cell_agent: AsyncAgentRunner) -> None:
        self.settings = settings
        self.cell_agent = cell_agent

    async def build_report(self, results: Iterable[PaperQAResult]) -> Path:
        """Generate the curator TSV report from PaperQA markdown outputs."""
        rows: list[dict[str, str]] = []
        for result in results:
            table = await self._load_or_convert_table(result)
            for entry in table:
                rows.append(
                    {
                        "Cell ID": result.cell_type.cl_id,
                        "Name": result.cell_type.name,
                        "Assertion": entry.get("assertion", ""),
                        "Agent Validation": str(entry.get("validated", "")),
                        "Curator Validation": "",
                        "References": result.cell_type.references,
                        "Curator Notes": "",
                        "Agent Notes": entry.get("summary_text", ""),
                    }
                )
        report_path = self.settings.paths.output_dir / "cell_type_validation_report.tsv"
        _write_tsv(report_path, rows)
        logger.info("Report generated at %s", report_path)
        return report_path

    async def _load_or_convert_table(self, result: PaperQAResult) -> list[dict]:
        cache_path = self.settings.paths.paperqa_json_dir / f"{result.cell_type.cl_id}.json"
        if cache_path.exists():
            return read_json(cache_path)
        prompt = (
            "From the following input, extract only the markdown table and convert it into a JSON "
            "array of objects. Each object should have the keys assertion, validated (True/False), "
            "summary_text, and references. Ignore all non-table text and output only the JSON. "
            f"Report:\n{result.report_markdown}\n"
        )
        response = await self.cell_agent.run(prompt)
        data = _parse_json_array(response)
        write_json(cache_path, data)
        return data


def _parse_json_array(output: str) -> list[dict]:
    candidate = output.replace("```json", "").replace("```", "").strip()
    data = json.loads(candidate)
    if not isinstance(data, list):
        raise ValueError("Agent output did not contain a JSON array.")
    return data


def _write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMN_NAMES, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


__all__ = ["ReportBuilder"]
