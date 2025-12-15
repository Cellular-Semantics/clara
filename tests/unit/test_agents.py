from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from clara.agents.cell_validation.cell_agent_config import get_cell_validation_config
from clara.agents.cell_validation.cell_agent_tools import read_json as agent_read_json
from clara.agents.cell_validation.cell_agent_tools import read_text as agent_read_text
from clara.agents.paperqa.paperqa_agent import PaperQAAgent

pytestmark = pytest.mark.unit


def test_cell_validation_config_creates_workdir(tmp_path: Path, monkeypatch) -> None:
    workdir = tmp_path / "work"
    monkeypatch.setenv("CLARA_WORKDIR", str(workdir))
    config = get_cell_validation_config()
    assert config.workdir == workdir
    assert workdir.exists()


def test_cell_agent_tools_readers(tmp_path: Path) -> None:
    text_file = tmp_path / "sample.txt"
    text_file.write_text("hello", encoding="utf-8")
    assert agent_read_text(None, str(text_file)) == "hello"

    json_file = tmp_path / "data.json"
    payload = {"value": 42}
    json_file.write_text(json.dumps(payload), encoding="utf-8")
    assert agent_read_json(None, str(json_file)) == payload


def test_paperqa_config_uses_environment(tmp_path: Path, monkeypatch) -> None:
    workdir = tmp_path / "paperqa"
    monkeypatch.setenv("CLARA_PAPERQA_MODEL", "fake-model")
    monkeypatch.setenv("CLARA_PAPERQA_TEMPERATURE", "0.5")
    monkeypatch.setenv("CLARA_PAPERQA_WORKDIR", str(workdir))
    import clara.agents.paperqa.paperqa_config as pq_config

    importlib.reload(pq_config)
    config = pq_config.get_paperqa_config()
    assert config.llm == "fake-model"
    assert config.temperature == 0.5
    assert config.workdir == workdir
    assert workdir.exists()


def test_paperqa_agent_runs_with_stub(monkeypatch) -> None:
    class DummyAgent:
        def __init__(self, *args, **kwargs) -> None:
            self.tools = []

        def tool(self, func):
            self.tools.append(func)
            return func

        async def run(self, prompt: str):
            return SimpleNamespace(output=f"answer:{prompt}")

    dummy_module = ModuleType("pydantic_ai")
    dummy_module.Agent = DummyAgent  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pydantic_ai", dummy_module)

    agent = PaperQAAgent()
    result = asyncio.run(agent.run("prompt"))
    assert result == "answer:prompt"
