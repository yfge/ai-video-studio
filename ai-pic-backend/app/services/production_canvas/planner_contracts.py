from __future__ import annotations

from app.schemas.production_canvas import (
    ProductionCanvasSavedEdge,
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
    ProductionCanvasViewport,
)
from app.schemas.production_canvas_planner import (
    ProductionCanvasPlannerProposal,
    ProductionCanvasPlannerStep,
)

from .planner_ports import (
    ALLOWED_BINDINGS,
    CANONICAL_DEPENDENCIES,
    REQUIRED_DEPENDENCIES,
    SKILL_PORTS,
    canvas_skill_node_id,
    canvas_skill_ports,
)


def canonical_canvas_planner_proposal(
    objective: str,
) -> ProductionCanvasPlannerProposal:
    return ProductionCanvasPlannerProposal(
        objective=objective,
        assumptions=["使用现有生产服务与人工媒体选用门槛。"],
        steps=[
            ProductionCanvasPlannerStep(
                skill=skill,
                reason="确定性完整生产方案。",
                depends_on=dependencies,
            )
            for skill, dependencies in CANONICAL_DEPENDENCIES.items()
        ],
    )


def _validate_dependencies(proposal: ProductionCanvasPlannerProposal) -> None:
    skills = [step.skill for step in proposal.steps]
    if len(skills) != len(set(skills)):
        raise ValueError("Planner skill ids must be unique")
    if skills[0] != "brief.compose":
        raise ValueError("Planner must start with brief.compose")
    positions = {skill: index for index, skill in enumerate(skills)}
    for step in proposal.steps:
        if step.skill not in SKILL_PORTS:
            raise ValueError(f"Unknown planner skill: {step.skill}")
        dependencies = set(step.depends_on)
        required = REQUIRED_DEPENDENCIES.get(step.skill, set())
        if not required.issubset(dependencies):
            missing = ", ".join(sorted(required - dependencies))
            raise ValueError(f"{step.skill} missing dependencies: {missing}")
        for dependency in dependencies:
            if dependency not in positions:
                raise ValueError(f"Unknown planner dependency: {dependency}")
            if positions[dependency] >= positions[step.skill]:
                raise ValueError("Planner dependencies must precede their target")
            if (dependency, step.skill) not in ALLOWED_BINDINGS:
                raise ValueError(
                    f"Unsupported planner dependency: {dependency} -> {step.skill}"
                )


def compile_canvas_planner_edges(
    proposal: ProductionCanvasPlannerProposal,
) -> list[ProductionCanvasSavedEdge]:
    _validate_dependencies(proposal)
    edges: list[ProductionCanvasSavedEdge] = []
    for step in proposal.steps:
        for dependency in step.depends_on:
            binding = ALLOWED_BINDINGS[(dependency, step.skill)]
            source = canvas_skill_node_id(dependency)
            target = canvas_skill_node_id(step.skill)
            edges.append(
                ProductionCanvasSavedEdge(
                    edge_id=(
                        f"{source}-{binding.from_port}-to-"
                        f"{target}-{binding.to_port}"
                    ),
                    from_node=source,
                    from_port=binding.from_port,
                    to_node=target,
                    to_port=binding.to_port,
                    binding_type=binding.binding_type,
                    required=True,
                )
            )
    _validate_compiled_graph(proposal, edges)
    return edges


def _validate_compiled_graph(
    proposal: ProductionCanvasPlannerProposal,
    edges: list[ProductionCanvasSavedEdge],
) -> None:
    nodes = []
    for index, step in enumerate(proposal.steps):
        inputs, outputs = canvas_skill_ports(step.skill)
        nodes.append(
            ProductionCanvasSavedNode(
                id=canvas_skill_node_id(step.skill),
                label=step.skill,
                title=step.skill,
                status="draft",
                x=index * 280,
                y=0,
                width=240,
                kind="pipeline",
                skill=step.skill,
                input_ports=inputs,
                output_ports=outputs,
            )
        )
    ProductionCanvasSavedState(
        graph_version=2,
        nodes=nodes,
        edges=edges,
        viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
    )
