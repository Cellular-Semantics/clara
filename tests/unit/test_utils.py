from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema import ValidationError

import clara as clara_module
from clara import bootstrap
from clara.utils import chunk_items, load_validation_settings
from clara.utils.io_utils import read_json, read_text, write_json, write_text
from clara.validation import ensure_services_registered, validate_workflow_output

pytestmark = pytest.mark.unit


def test_bootstrap_with_custom_path(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("TEST=1", encoding="utf-8")
    called: dict[str, str | None] = {}

    def fake_load(path: str | None = None) -> None:
        called["path"] = path

    monkeypatch.setattr(clara_module, "load_dotenv", fake_load)
    bootstrap(str(env_file))
    assert called["path"] == str(env_file)


def test_bootstrap_without_path(monkeypatch) -> None:
    called: dict[str, str | None] = {}

    def fake_load(path: str | None = None) -> None:
        called["path"] = path

    monkeypatch.setattr(clara_module, "load_dotenv", fake_load)
    bootstrap()
    assert called["path"] is None


def test_load_validation_settings_handles_env(tmp_path: Path) -> None:
    base = tmp_path / "envdata"
    env = {
        "CLARA_CELL_DATA_DIR": str(base),
        "CLARA_IS_TEST_MODE": "true",
        "CLARA_TEST_TERMS": "A,B , C",
        "CLARA_FALSE_ASSERTION_PROBABILITY": "0.2",
    }
    settings = load_validation_settings(env)
    assert settings.is_test_mode is True
    assert settings.test_terms == ("A", "B", "C")
    assert settings.false_assertion_probability == 0.2
    settings.paths.ensure_directories()
    assert (base / "output").exists()


def test_chunk_items_batches_sequences() -> None:
    batches = chunk_items([1, 2, 3, 4, 5], size=2)
    assert batches == [[1, 2], [3, 4], [5]]


def test_io_utils_round_trip(tmp_path: Path) -> None:
    text_path = tmp_path / "note.txt"
    json_path = tmp_path / "data.json"
    write_text(text_path, "content")
    assert read_text(text_path) == "content"
    write_json(json_path, {"value": 7})
    assert read_json(json_path) == {"value": 7}


def test_validate_workflow_output_and_service_registry() -> None:
    payload = {
        "status": "completed",
        "summary": "done",
        "actions": [{"name": "fetch"}],
        "warnings": [],
    }
    validate_workflow_output(payload)

    with pytest.raises(ValidationError):
        validate_workflow_output({"status": "bad", "summary": "oops"})

    ensure_services_registered(["svc1"], ["svc1", "svc2"])
    with pytest.raises(ValidationError):
        ensure_services_registered(["svc1", "missing"], ["svc1"])
