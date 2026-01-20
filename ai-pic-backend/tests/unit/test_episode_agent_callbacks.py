import asyncio
import json

import pytest

from app.services.episode_agent import EpisodeGenerationCallbacks, EpisodeLangGraphAgent
from app.services.providers.base import AIModelType, AIResponse, AITaskType


class FakeGraph:
    """Minimal graph runner to avoid langgraph dependency in tests."""

    def __init__(self, _state_type):
        self.nodes = {}
        self.edges = {}
        self.entry = None

    def add_node(self, name, fn):
        self.nodes[name] = fn

    def add_edge(self, src, dst):
        self.edges.setdefault(src, []).append(dst)

    def set_entry_point(self, name):
        self.entry = name

    def compile(self):
        nodes = self.nodes
        edges = self.edges
        entry = self.entry

        class Runner:
            async def ainvoke(self, state):
                current = entry
                data = state
                while current and current != "END":
                    fn = nodes[current]
                    if asyncio.iscoroutinefunction(fn):
                        data = await fn(data)
                    else:
                        data = fn(data)
                    next_nodes = edges.get(current, [])
                    current = next_nodes[0] if next_nodes else None
                return data

        return Runner()


class CapturingAIManager:
    def __init__(self, responses):
        self._responses = responses
        self.prompts = []

    async def generate_text(self, *args, **kwargs):
        self.prompts.append(kwargs.get("prompt"))
        return self._responses.pop(0)


def make_response(data: str) -> AIResponse:
    return AIResponse(
        success=True,
        data=data,
        error=None,
        provider="mock",
        model="mock-model",
        task_type=AITaskType.STORY_GENERATION,
        model_type=AIModelType.TEXT_GENERATION,
        usage={"total_tokens": 10},
        metadata={},
    )

def make_audit_pass_response() -> AIResponse:
    return make_response(json.dumps({"verdict": "pass", "issues": []}))


def make_ledger_update_response(episode_number: int) -> AIResponse:
    return make_response(
        json.dumps(
            {
                "ledger": {},
                "episode_snapshot": {"episode_number": episode_number},
            }
        )
    )


@pytest.mark.asyncio
async def test_episode_agent_callbacks_emit_and_fallback(monkeypatch):
    monkeypatch.setattr("app.services.episode_agent.LANGGRAPH_AVAILABLE", True)
    monkeypatch.setattr("app.services.episode_agent.StateGraph", FakeGraph)
    monkeypatch.setattr("app.services.episode_agent.END", "END")

    outline = {
        "episodes": [
            {"episode_number": 1, "title": "E1", "logline": "L1"},
            {"episode_number": 2, "title": "E2", "logline": "L2"},
        ]
    }
    episode_ok = {
        "episodes": [
            {
                "episode_number": 1,
                "title": "E1",
                "summary": "S1",
                "conflicts": [{"description": "c", "intensity": "low"}],
            }
        ]
    }

    ai_manager = CapturingAIManager(
        [
            make_response(json.dumps(outline)),
            make_response(json.dumps(episode_ok)),
            make_audit_pass_response(),
            make_ledger_update_response(1),
            make_response("not-json"),  # triggers outline-based fallback for episode 2
            make_ledger_update_response(2),
        ]
    )

    class Svc:
        def __init__(self):
            self.ai_manager = ai_manager

    progress: list[str] = []
    outlines: list[tuple[dict, dict]] = []
    episodes: list[tuple[dict, dict]] = []

    def on_outline(outlines_obj: dict, meta: dict) -> None:
        outlines.append((outlines_obj, meta))

    def on_episode(episode_obj: dict, meta: dict) -> None:
        episodes.append((episode_obj, meta))

    agent = EpisodeLangGraphAgent(Svc())
    result = await agent.generate(
        story={"title": "T", "genre": "drama"},
        episode_count=2,
        episode_duration=None,
        focus_characters=[{"id": 1, "name": "文闻", "description": "desc"}],
        plot_complexity="medium",
        pacing="medium",
        additional_requirements=None,
        style_preferences=None,
        model=None,
        prefer_provider=None,
        temperature=0.7,
        callbacks=EpisodeGenerationCallbacks(
            on_progress=progress.append,
            on_outline=on_outline,
            on_episode=on_episode,
        ),
    )

    assert result is not None
    assert len(outlines) == 1
    assert len(episodes) == 2

    assert any(msg.startswith("剧集大纲：") for msg in progress)
    assert any(msg == "生成第1集：调用模型" for msg in progress)
    assert any(msg == "生成第2集：调用模型" for msg in progress)

    episode_2_obj, episode_2_meta = episodes[1]
    assert episode_2_obj.get("fallback_from_outline") is True
    assert episode_2_meta.get("fallback_from_outline") is True

    episode_prompts = [
        p
        for p in ai_manager.prompts
        if isinstance(p, str) and "当前集的 Step Outline" in p
    ]
    assert episode_prompts
    assert "重点角色：文闻" in episode_prompts[0]
