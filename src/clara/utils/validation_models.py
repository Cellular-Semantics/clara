"""Shared data models for the CL validation workflow."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CellTypeInfo:
    """Representation of a curated CL entry and its reference packet metadata."""

    cl_id: str
    name: str
    definition: str
    logical_axioms: str
    source: str
    has_all_references: bool
    references: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> CellTypeInfo:
        """Parse a cell-type entry loaded from JSON/TSV sources."""
        return cls(
            cl_id=str(payload["cell_id"]),
            name=str(payload["name"]),
            definition=str(payload["definition"]),
            logical_axioms=str(payload.get("relations", "")),
            source=str(payload.get("source", "")),
            has_all_references=bool(payload.get("has_all_references", False)),
            references=str(payload.get("references", "")),
        )

    def to_payload(self) -> dict[str, Any]:
        """Serialize the model for caching or report generation."""
        return {
            "cell_id": self.cl_id,
            "name": self.name,
            "definition": self.definition,
            "relations": self.logical_axioms,
            "source": self.source,
            "has_all_references": self.has_all_references,
            "references": self.references,
        }


@dataclass
class PaperQAResult:
    """Cached PaperQA output per cell type."""

    cell_type: CellTypeInfo
    report_markdown: str


@dataclass
class ValidationState:
    """Mutable state shared between workflow steps."""

    cl_definitions: list[CellTypeInfo] = field(default_factory=list)
    cl_updated_definitions: list[CellTypeInfo] = field(default_factory=list)
    paperqa_results: list[PaperQAResult] = field(default_factory=list)
    is_test_mode: bool = False

    def extend_definitions(self, entries: Iterable[CellTypeInfo]) -> None:
        """Add curated definitions before negative-test seeding."""
        self.cl_definitions.extend(entries)

    def extend_updated_definitions(self, entries: Iterable[CellTypeInfo]) -> None:
        """Add mutated definitions that will be sent through PaperQA."""
        self.cl_updated_definitions.extend(entries)

    def append_paperqa_result(self, result: PaperQAResult) -> None:
        """Cache a PaperQA markdown report."""
        self.paperqa_results.append(result)


__all__ = ["CellTypeInfo", "PaperQAResult", "ValidationState"]
