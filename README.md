# Clara – Cell Ontology Validation Pipeline

[![Tests](https://github.com/Cellular-Semantics/clara/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Cellular-Semantics/clara/actions/workflows/test.yml)
[![coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Cellular-Semantics/clara/main/.github/badges/coverage.json)](https://github.com/Cellular-Semantics/clara/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-managed-6C4E81.svg)](https://github.com/astral-sh/uv)

Clara ingests curated Cell Ontology definitions, injects synthetic negative assertions, and runs PaperQA plus a cell-validation agent to vet every atomic statement against the reference packet. The workflow outputs curator-ready TSV reports with assertions, automated verdicts, and supporting literature so ontology editors can focus on the true discrepancies.

---

## 1. Prerequisites

- **Python 3.11+**
- **uv** (dependency manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- `.env` at repo root containing:

  ```bash
  OPENAI_API_KEY=sk-...
  ANTHROPIC_API_KEY=sk-ant-...
  ```

These keys are required for the PaperQA and cell-validation agents. The `clara.bootstrap()` helper loads `.env` automatically via `python-dotenv`.

---

## 2. Install & Bootstrap

```bash
git clone https://github.com/Cellular-Semantics/clara.git
cd clara

uv sync --dev
uv run pre-commit install          # optional but recommended
git config core.hooksPath .githooks
```

The pre-commit hook runs Ruff lint/format, unit tests, and (when keys are present) the integration test suite so failures are caught before pushing.

---

## 3. Sample Data Layout

Small fixture data live under `tests/data/` and get cloned into a temp directory whenever the integration tests or CLI run in test mode. A real run expects the following structure beneath `CLARA_CELL_DATA_DIR` (defaults to `data/`):

```
data/
├── cells_data.json          # curated CL entries with references
├── reference/               # reference packets per CL ID
└── output/                  # generated TSV + caches (auto-created)
```

Feel free to point `CLARA_CELL_DATA_DIR` to another location; the workflow creates `output/`, `pqa_jsons/`, and other caches on demand.

---

## 4. Running the Validation Workflow

### CLI

```bash
uv run python scripts/cl_validation.py --cell-data-dir data --test-mode
```

The CLI orchestrates four nodes:

1. **load_definitions** – read curated entries, filter for references + test scope.
2. **seed_false_assertions** – reuse cached negatives or generate new ones via the cell agent.
3. **run_paperqa** – call PaperQA for each mutated definition and cache markdown responses.
4. **generate_report** – convert PaperQA tables into TSV rows for curator review.

This command copies the curated data into a scratch workspace (if `--test-mode` is set), validates the workflow graph, and executes each node in sequence. The CLI returns the path to `output/cell_type_validation_report.tsv` once PaperQA and report generation complete.

### Programmatic API

Embed the workflow inside another Python process when you need finer control over settings or want to call the pipeline from notebooks / services:

```python
import asyncio
from pathlib import Path

from clara import bootstrap
from clara.graphs import run_cl_validation_workflow
from clara.utils import load_validation_settings

# Load .env so agent clients have API keys
bootstrap()

# Customize settings before running (optional)
settings = load_validation_settings()
settings.paths.cell_data_dir = Path("/path/to/cell-data")
# settings.is_test_mode = True
# settings.test_terms = ("CL_4052001",)

# Execute the graph and capture the TSV path
report_path = asyncio.run(run_cl_validation_workflow(settings=settings))
print(f"Report written to {report_path}")
```

`load_validation_settings()` reads all relevant environment variables so you can override paths, test mode, or probabilities without changing code. Pass custom `cell_agent` / `paperqa_agent` implementations into `run_cl_validation_workflow` if you need to stub the LLM layer in tests.

---

## 5. Architecture

```
src/clara/
├── agents/                # Cell validation + PaperQA agents (pydantic-ai)
├── graphs/                # CL validation workflow graph + orchestration helpers
├── services/              # Dataset loader, false assertion seeder, PaperQA + report services
├── utils/                 # Validation config, IO helpers, data models
├── schemas/               # JSON Schema loader for workflow outputs
└── validation/            # Graph + service validation utilities
scripts/                   # CLI + CI helpers
tests/unit/                # Fast, isolated tests (agents, services, utils, graph)
tests/integration/         # Real end-to-end pipeline against fixture data
```

- **Agents** wrap Pydantic AI models so we can lazily spin up LLM clients with shared tooling (file-reading tools, dependency injection).
- **Services** provide deterministic building blocks: dataset loading, synthetic negative seeding, PaperQA execution with caching, and TSV report generation.
- **Graph** defines the workflow order using `pydantic_graph` and `pydantic_ai` so every transition is validated at runtime.
- **Utils** centralize configuration loading (`ValidationSettings`), IO helpers, and state models, keeping services thin.

---

## 6. Testing

```bash
uv run pytest -m unit           # unit tests only
uv run pytest -m integration    # requires OPENAI/ANTHROPIC keys and sample data
```

- Unit tests stub the agents/services to stay deterministic.
- Integration tests copy `tests/data` into a temp workspace, set the appropriate env vars, and run the real workflow end-to-end. They fail fast if API keys are missing.
- Coverage is tracked via `.github/badges/coverage.json`; regenerate it with `uv run pytest --cov=src/clara --cov-report=xml` followed by `uv run python scripts/ci/update_coverage_badge.py`.

CI runs only `uv run pytest -m unit` on Python 3.11. Developers are expected to run the integration suite locally before pushing.

---

## 7. Development Workflow

1. Follow the rules in `CLAUDE.md` (tests first, no skipped failures, real integrations).
2. Install deps with `uv sync --dev`.
3. Use the git hooks (`git config core.hooksPath .githooks`) to run lint + tests automatically.
4. Before committing:

   ```bash
   uv run ruff check --fix src/ tests/
   uv run ruff format src/ tests/
   uv run mypy src/
   uv run pytest -m unit
   uv run pytest -m integration   # requires keys
   ```

5. Documentation is managed via Sphinx (`python scripts/check-docs.py`), though the initial scaffolding is still pending.

---

## 8. Contributing

- Ensure new features include both unit and integration coverage where applicable.
- Keep curated fixtures under `tests/data` small so integration tests stay fast.
- When adding new agents/services, expose them through the appropriate `__init__.py` to keep the public API tidy.
- Open PRs with a brief summary plus testing evidence (unit + integration commands run locally).

---

## License

MIT – see [LICENSE](LICENSE).

MIT License - see `LICENSE` for details.
