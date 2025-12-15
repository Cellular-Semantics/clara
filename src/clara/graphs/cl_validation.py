"""CL validation workflow definition and orchestration helpers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path

from ..agents import PaperQAAgent, build_paperqa_agent
from ..services import (
    CellAgentAdapter,
    CellDatasetLoader,
    FalseAssertionService,
    PaperQAService,
    ReportBuilder,
)
from ..services.agent_adapters import AsyncAgentRunner
from ..utils import ValidationSettings, load_validation_settings
from ..utils.validation_models import ValidationState
from .definitions import GraphNode, WorkflowGraph
from .graph_agent import GraphDependencies


def build_cl_validation_graph() -> WorkflowGraph:
    """Declarative workflow describing the CL validation pipeline."""

    nodes = [
        GraphNode(
            id="load_definitions",
            description="Load curated CL definitions from disk.",
            service="cl.validation.load_definitions",
            next=["seed_false_assertions"],
        ),
        GraphNode(
            id="seed_false_assertions",
            description="Inject synthetic negatives into curated definitions.",
            service="cl.validation.seed_false_assertions",
            next=["run_paperqa"],
        ),
        GraphNode(
            id="run_paperqa",
            description="Run PaperQA for each updated definition and cache outputs.",
            service="cl.validation.run_paperqa",
            next=["generate_report"],
        ),
        GraphNode(
            id="generate_report",
            description="Convert cached PaperQA outputs into a curator TSV report.",
            service="cl.validation.generate_report",
            next=[],
        ),
    ]

    return WorkflowGraph(
        name="cl_validation",
        entrypoint="load_definitions",
        nodes=nodes,
    )


@dataclass
class ClValidationGraphDependencies(GraphDependencies):
    """Graph dependencies bundled with CL validation services."""

    settings: ValidationSettings = field(default_factory=load_validation_settings)
    state: ValidationState = field(default_factory=ValidationState)
    dataset_loader: CellDatasetLoader | None = None
    false_service: FalseAssertionService | None = None
    paperqa_service: PaperQAService | None = None
    report_builder: ReportBuilder | None = None
    cell_agent: AsyncAgentRunner | None = None
    paperqa_agent: PaperQAAgent | None = None
    report_path: Path | None = None

    def __post_init__(self) -> None:
        self.settings.paths.ensure_directories()
        agent = self.cell_agent or CellAgentAdapter()
        self.dataset_loader = self.dataset_loader or CellDatasetLoader(self.settings)
        self.false_service = self.false_service or FalseAssertionService(self.settings, agent)
        self.paperqa_service = self.paperqa_service or PaperQAService(
            self.settings, agent=self.paperqa_agent or build_paperqa_agent()
        )
        self.report_builder = self.report_builder or ReportBuilder(self.settings, agent)
        self.state.is_test_mode = self.settings.is_test_mode


NodeHandler = Callable[[ClValidationGraphDependencies], Awaitable[str | None]]


async def run_cl_validation_graph(
    *,
    settings: ValidationSettings | None = None,
    deps: ClValidationGraphDependencies | None = None,
    cell_agent: AsyncAgentRunner | None = None,
    paperqa_agent: PaperQAAgent | None = None,
) -> Path:
    """Execute the CL validation workflow graph using the registered handlers."""

    graph = build_cl_validation_graph()
    if deps is None:
        deps = ClValidationGraphDependencies(
            graph=graph,
            settings=settings or load_validation_settings(),
            cell_agent=cell_agent,
            paperqa_agent=paperqa_agent,
        )
    else:
        if settings or cell_agent or paperqa_agent:
            raise ValueError(
                "Custom settings or agents cannot be provided when dependencies are supplied."
            )
        deps.graph = graph

    node_id: str | None = graph.entrypoint
    while node_id:
        node = deps.graph.route(node_id)
        handler = _SERVICE_HANDLERS.get(node.service)
        if not handler:
            raise ValueError(f"No service handler registered for '{node.service}'")
        node_id = await handler(deps)

    if not deps.report_path:
        raise RuntimeError("CL validation workflow completed without generating a report.")
    return deps.report_path


async def _handle_load_definitions(deps: ClValidationGraphDependencies) -> str:
    loader = deps.dataset_loader
    if not loader:
        raise RuntimeError("Dataset loader not configured.")
    definitions = loader.load_definitions()
    deps.state.cl_definitions.clear()
    deps.state.extend_definitions(definitions)
    return "seed_false_assertions"


async def _handle_seed_false_assertions(deps: ClValidationGraphDependencies) -> str:
    service = deps.false_service
    if not service:
        raise RuntimeError("False assertion service not configured.")
    definitions = deps.state.cl_definitions
    mutated = await service.seed_definitions(definitions)
    deps.state.cl_updated_definitions.clear()
    deps.state.extend_updated_definitions(mutated)
    return "run_paperqa"


async def _handle_run_paperqa(deps: ClValidationGraphDependencies) -> str:
    service = deps.paperqa_service
    if not service:
        raise RuntimeError("PaperQA service not configured.")
    results = await service.validate_cells(deps.state.cl_updated_definitions)
    deps.state.paperqa_results.clear()
    for result in results:
        deps.state.append_paperqa_result(result)
    return "generate_report"


async def _handle_generate_report(deps: ClValidationGraphDependencies) -> None:
    builder = deps.report_builder
    if not builder:
        raise RuntimeError("Report builder not configured.")
    report_path = await builder.build_report(deps.state.paperqa_results)
    deps.report_path = report_path
    return None


_SERVICE_HANDLERS: dict[str, NodeHandler] = {
    "cl.validation.load_definitions": _handle_load_definitions,
    "cl.validation.seed_false_assertions": _handle_seed_false_assertions,
    "cl.validation.run_paperqa": _handle_run_paperqa,
    "cl.validation.generate_report": _handle_generate_report,
}


async def run_cl_validation_workflow(
    settings: ValidationSettings | None = None,
    cell_agent: AsyncAgentRunner | None = None,
    paperqa_agent: PaperQAAgent | None = None,
) -> Path:
    """Compatibility wrapper that executes the CL validation graph."""

    return await run_cl_validation_graph(
        settings=settings,
        cell_agent=cell_agent,
        paperqa_agent=paperqa_agent,
    )


__all__ = [
    "build_cl_validation_graph",
    "ClValidationGraphDependencies",
    "run_cl_validation_graph",
    "run_cl_validation_workflow",
]
