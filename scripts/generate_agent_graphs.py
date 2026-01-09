#!/usr/bin/env python3
"""Generate agent state diagrams (Mermaid + PNG) for README/docs.

This script intentionally builds *diagram-only* LangGraph StateGraphs with
TypedDict state to avoid draw-time channel conflicts for conditional edges.
It does NOT execute any agent logic.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, TypedDict

from langgraph.graph import END, StateGraph


class DiagramState(TypedDict, total=False):
    """Minimal state schema used only for diagram rendering."""

    dummy: int


def _noop(_: DiagramState) -> dict:
    return {}


def _always(value: str) -> Callable[[DiagramState], str]:
    def _route(_: DiagramState) -> str:
        return value

    return _route


def build_story_langgraph_agent_graph() -> StateGraph:
    """Conceptual flow for StoryLangGraphAgent (draft → validate → repair loop)."""
    graph = StateGraph(DiagramState)
    graph.add_node("draft", _noop)
    graph.add_node("validate_schema", _noop)
    graph.add_node("repair_output", _noop)
    graph.add_node("fail", _noop)

    graph.set_entry_point("draft")
    graph.add_edge("draft", "validate_schema")
    graph.add_conditional_edges(
        "validate_schema",
        _always("repair"),
        {
            "ok": END,
            "repair": "repair_output",
            "fail": "fail",
        },
    )
    graph.add_edge("repair_output", "validate_schema")
    graph.add_edge("fail", END)
    return graph


def build_episode_langgraph_agent_graph() -> StateGraph:
    """Conceptual flow for EpisodeLangGraphAgent (outline → episodes)."""
    graph = StateGraph(DiagramState)
    graph.add_node("generate_step_outline", _noop)
    graph.add_node("validate_outline", _noop)
    graph.add_node("generate_episodes", _noop)
    graph.add_node("fail", _noop)

    graph.set_entry_point("generate_step_outline")
    graph.add_edge("generate_step_outline", "validate_outline")
    graph.add_conditional_edges(
        "validate_outline",
        _always("ok"),
        {
            "ok": "generate_episodes",
            "fail": "fail",
        },
    )
    graph.add_edge("generate_episodes", END)
    graph.add_edge("fail", END)
    return graph


def build_script_langgraph_agent_graph() -> StateGraph:
    """Flow for ScriptLangGraphAgent (scene_plan → dialogues → review → assemble)."""
    graph = StateGraph(DiagramState)
    graph.add_node("scene_plan", _noop)
    graph.add_node("dialogue", _noop)
    graph.add_node("react_validate", _noop)
    graph.add_node("review", _noop)
    graph.add_node("assemble", _noop)

    graph.set_entry_point("scene_plan")
    graph.add_edge("scene_plan", "dialogue")
    graph.add_edge("dialogue", "react_validate")
    graph.add_conditional_edges(
        "react_validate",
        _always("review"),
        {
            "retry_dialogue": "dialogue",
            "review": "review",
        },
    )
    graph.add_edge("review", "assemble")
    graph.add_edge("assemble", END)
    return graph


def build_storyboard_react_reasoner_graph() -> StateGraph:
    """Flow for StoryboardReActReasoner (plan → critique → finalize)."""
    graph = StateGraph(DiagramState)
    graph.add_node("plan", _noop)
    graph.add_node("critique", _noop)
    graph.add_node("finalize", _noop)
    graph.set_entry_point("plan")
    graph.add_edge("plan", "critique")
    graph.add_edge("critique", "finalize")
    graph.add_edge("finalize", END)
    return graph


def build_timeline_langgraph_agent_graph() -> StateGraph:
    """Flow for TimelineLangGraphAgent."""
    graph = StateGraph(DiagramState)
    graph.add_node("analyze_scene", _noop)
    graph.add_node("think_timing", _noop)
    graph.add_node("propose_gaps", _noop)
    graph.add_node("validate_rhythm", _noop)
    graph.add_node("adjust_timing", _noop)
    graph.add_node("finalize", _noop)

    graph.set_entry_point("analyze_scene")
    graph.add_edge("analyze_scene", "think_timing")
    graph.add_edge("think_timing", "propose_gaps")
    graph.add_edge("propose_gaps", "validate_rhythm")
    graph.add_conditional_edges(
        "validate_rhythm",
        _always("finalize"),
        {
            "finalize": "finalize",
            "adjust_timing": "adjust_timing",
        },
    )
    graph.add_edge("adjust_timing", "validate_rhythm")
    graph.add_edge("finalize", END)
    return graph


def build_duration_orchestrator_agent_graph() -> StateGraph:
    """Flow for DurationOrchestratorAgent."""
    graph = StateGraph(DiagramState)
    graph.add_node("allocate_budget", _noop)
    graph.add_node("generate_dialogue", _noop)
    graph.add_node("tts_trial", _noop)
    graph.add_node("validate_duration", _noop)
    graph.add_node("commit_scene", _noop)
    graph.add_node("prepare_retry", _noop)
    graph.add_node("assemble_episode", _noop)
    graph.add_node("final_validation", _noop)

    graph.set_entry_point("allocate_budget")
    graph.add_conditional_edges(
        "allocate_budget",
        _always("generate"),
        {
            "generate": "generate_dialogue",
            "assemble": "assemble_episode",
            "failed": END,
        },
    )
    graph.add_conditional_edges(
        "generate_dialogue",
        _always("tts"),
        {
            "tts": "tts_trial",
            "retry": "generate_dialogue",
            "failed": END,
        },
    )
    graph.add_edge("tts_trial", "validate_duration")
    graph.add_conditional_edges(
        "validate_duration",
        _always("commit"),
        {
            "commit": "commit_scene",
            "retry": "prepare_retry",
            "next": "commit_scene",
        },
    )
    graph.add_edge("prepare_retry", "generate_dialogue")
    graph.add_conditional_edges(
        "commit_scene",
        _always("continue"),
        {
            "continue": "generate_dialogue",
            "assemble": "assemble_episode",
        },
    )
    graph.add_edge("assemble_episode", "final_validation")
    graph.add_edge("final_validation", END)
    return graph


def _write_graph_assets(
    *,
    output_dir: Path,
    slug: str,
    graph: StateGraph,
) -> None:
    app = graph.compile()
    runnable_graph = app.get_graph()
    mermaid = runnable_graph.draw_mermaid()
    png = runnable_graph.draw_mermaid_png()

    (output_dir / f"{slug}.mmd").write_text(mermaid, encoding="utf-8")
    (output_dir / f"{slug}.png").write_bytes(png)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Mermaid + PNG agent state diagrams into docs/agent_graphs/."
    )
    parser.add_argument(
        "--output-dir",
        default="docs/agent_graphs",
        help="Output directory (default: docs/agent_graphs).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    graphs = [
        ("story_langgraph_agent", build_story_langgraph_agent_graph()),
        ("episode_langgraph_agent", build_episode_langgraph_agent_graph()),
        ("script_langgraph_agent", build_script_langgraph_agent_graph()),
        ("storyboard_react_reasoner", build_storyboard_react_reasoner_graph()),
        ("timeline_langgraph_agent", build_timeline_langgraph_agent_graph()),
        ("duration_orchestrator_agent", build_duration_orchestrator_agent_graph()),
    ]

    for slug, graph in graphs:
        _write_graph_assets(output_dir=output_dir, slug=slug, graph=graph)

    print(f"[agent_graphs] Wrote {len(graphs)} graphs to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
