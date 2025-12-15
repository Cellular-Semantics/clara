from __future__ import annotations

import os
from pathlib import Path

import pytest

from clara import bootstrap

REQUIRED_ENV_VARS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


@pytest.mark.integration
def test_required_api_keys_present() -> None:
    """Ensure developers configure real API keys before running integrations."""
    if ROOT_ENV.exists():
        bootstrap(str(ROOT_ENV))
    else:
        bootstrap()
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    assert not missing, f"Missing integration environment variables: {missing}"
