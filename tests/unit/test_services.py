from __future__ import annotations

import asyncio

import pytest

from clara.services.agent_adapters import CellAgentAdapter

pytestmark = pytest.mark.unit


def test_cell_agent_adapter_uses_injected_agent(monkeypatch) -> None:
    class DummyAgent:
        def __init__(self) -> None:
            self.prompts: list[str] = []

        async def run(self, prompt: str) -> str:
            self.prompts.append(prompt)
            return "ok"

    dummy = DummyAgent()
    monkeypatch.setattr("clara.services.agent_adapters.build_cell_validation_agent", lambda: dummy)
    adapter = CellAgentAdapter()
    result = asyncio.run(adapter.run("ping"))
    assert result == "ok"
    assert dummy.prompts == ["ping"]
