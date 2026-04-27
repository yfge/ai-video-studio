"""Tests for generated agent graph documentation drift."""

from __future__ import annotations

from pathlib import Path

EXPECTED_STATEGRAPH_DOCS = {
    "script_langgraph_agent",
    "storyboard_pipeline",
    "storyboard_react_reasoner",
    "timeline_langgraph_agent",
    "duration_orchestrator_agent",
}

LEGACY_STRUCTURED_LOOP_DOCS = {
    "story_langgraph_agent",
    "episode_langgraph_agent",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_agent_graph_docs_match_real_stategraph_registry():
    root = _repo_root()
    docs_dir = root / "docs" / "agent_graphs"
    mmd_stems = {path.stem for path in docs_dir.glob("*.mmd")}
    png_stems = {path.stem for path in docs_dir.glob("*.png")}

    assert mmd_stems == EXPECTED_STATEGRAPH_DOCS
    assert png_stems == EXPECTED_STATEGRAPH_DOCS

    generator = (root / "scripts" / "generate_agent_graphs.py").read_text()
    for stem in EXPECTED_STATEGRAPH_DOCS:
        assert f'("{stem}",' in generator
    for stem in LEGACY_STRUCTURED_LOOP_DOCS:
        assert stem not in generator

    for readme_name in ("README.md", "README_EN.md"):
        readme = (root / readme_name).read_text()
        for stem in EXPECTED_STATEGRAPH_DOCS:
            assert f"docs/agent_graphs/{stem}.png" in readme
            assert f"docs/agent_graphs/{stem}.mmd" in readme
        for stem in LEGACY_STRUCTURED_LOOP_DOCS:
            assert f"docs/agent_graphs/{stem}." not in readme
