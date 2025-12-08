from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from clara.graphs import run_cl_validation_workflow
from clara.utils import ValidationPaths, ValidationSettings


class StubCellAgent:
    async def run(self, prompt: str) -> str:
        if "Insert a biologically plausible" in prompt:
            return json.dumps(
                {
                    "updated_definition": "Updated definition with false assertion.",
                    "false_assertion": "False assertion.",
                }
            )
        if "extract only the markdown table" in prompt:
            return json.dumps(
                [
                    {
                        "assertion": "Test assertion",
                        "validated": True,
                        "summary_text": "Evidence summary",
                        "references": "PMID:1",
                    }
                ]
            )
        raise AssertionError(f"Unexpected prompt: {prompt}")


class StubPaperQAAgent:
    async def run(self, prompt: str) -> str:
        if "For the following text" in prompt:
            return (
                "| Assertion | Validated | Evidence | References |\n"
                "| Test assertion | True | Evidence summary | PMID:1 |\n"
            )
        raise AssertionError(f"Unexpected PaperQA prompt: {prompt}")


@pytest.fixture
def validation_settings(tmp_path: Path) -> ValidationSettings:
    cell_data_dir = tmp_path / "data"
    references_dir = cell_data_dir / "reference" / "CL_0000001"
    references_dir.mkdir(parents=True)
    dataset_file = cell_data_dir / "cells_data.json"
    payload = {
        "CL_0000001": {
            "cell_id": "CL_0000001",
            "name": "Test Cell",
            "definition": "Original definition.",
            "relations": "is_a test.",
            "source": "test",
            "has_all_references": True,
            "references": "PMID:1",
        }
    }
    dataset_file.parent.mkdir(parents=True, exist_ok=True)
    dataset_file.write_text(json.dumps(payload), encoding="utf-8")
    output_dir = cell_data_dir / "output"
    paths = ValidationPaths(
        cell_data_dir=cell_data_dir,
        dataset_file=dataset_file,
        references_dir=cell_data_dir / "reference",
        output_dir=output_dir,
        false_definitions_file=output_dir / "cells_false_data.json",
        paperqa_markdown_dir=output_dir,
        paperqa_json_dir=output_dir / "pqa_jsons",
    )
    return ValidationSettings(
        paths=paths,
        is_test_mode=True,
        test_terms=("CL_0000001",),
        false_assertion_probability=1.0,
    )


def test_workflow_generates_report(validation_settings: ValidationSettings) -> None:
    stub_agent = StubCellAgent()
    report_path = asyncio.run(
        run_cl_validation_workflow(
            validation_settings,
            cell_agent=stub_agent,
            paperqa_agent=StubPaperQAAgent(),
        )
    )
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "CL_0000001" in content
    assert "Test assertion" in content


pytestmark = pytest.mark.unit
