from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import pytest

from clara import bootstrap
from clara.graphs import run_cl_validation_workflow
from clara.utils import load_validation_settings

TEST_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@pytest.mark.integration
def test_cl_validation_pipeline_real_agents(monkeypatch, tmp_path) -> None:
    if ENV_PATH.exists():
        bootstrap(str(ENV_PATH))
    else:
        bootstrap()

    integration_data_dir = tmp_path / "data"
    integration_data_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEST_DATA_DIR, integration_data_dir, dirs_exist_ok=True)

    monkeypatch.setenv("CLARA_CELL_DATA_DIR", str(integration_data_dir))
    # monkeypatch.setenv("CLARA_IS_TEST_MODE", "true")
    # monkeypatch.setenv("CLARA_TEST_TERMS", "CL_4052001")
    monkeypatch.setenv("CLARA_FALSE_ASSERTION_PROBABILITY", "0.0")

    settings = load_validation_settings()
    report_path = asyncio.run(run_cl_validation_workflow(settings=settings))
    expected_output = integration_data_dir / "output" / "cell_type_validation_report.tsv"
    assert report_path == expected_output
    assert expected_output.exists()
    contents = expected_output.read_text(encoding="utf-8")
    assert "CL_4052001" in contents
