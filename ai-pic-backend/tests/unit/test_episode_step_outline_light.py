import asyncio
import json

import pytest

from app.services.episode_agent import EpisodeLangGraphAgent
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


class FakeAIManager:
    def __init__(self, responses):
        self._responses = responses

    async def generate_text(self, *args, **kwargs):
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


@pytest.mark.asyncio
async def test_outline_logline_only(monkeypatch):
    monkeypatch.setattr("app.services.episode_agent.LANGGRAPH_AVAILABLE", True)
    monkeypatch.setattr("app.services.episode_agent.StateGraph", FakeGraph)
    monkeypatch.setattr("app.services.episode_agent.END", "END")

    outline = {"episodes": [{"episode_number": 1, "title": "E1", "logline": "钩子"}]}
    episode = {
        "episodes": [
            {
                "episode_number": 1,
                "title": "E1",
                "summary": "S",
                "conflicts": [{"description": "c", "intensity": "low"}],
            }
        ]
    }

    ai_manager = FakeAIManager(
        [
            make_response(json.dumps(outline)),
            make_response(json.dumps(episode)),
        ]
    )

    class Svc:
        def __init__(self):
            self.ai_manager = ai_manager

    agent = EpisodeLangGraphAgent(Svc())
    result = await agent.generate(
        story={"title": "T", "genre": "drama"},
        episode_count=1,
        episode_duration=None,
        focus_characters=None,
        plot_complexity="medium",
        pacing="medium",
        additional_requirements=None,
        style_preferences=None,
        model=None,
        prefer_provider=None,
        temperature=0.7,
    )

    assert result is not None
    assert result["normalized"]["episodes"][0]["title"] == "E1"
    assert result["step_outlines"]["episodes"][0]["logline"] == "钩子"
    assert result.get("prompt")  # prompt propagated for storage


@pytest.mark.asyncio
async def test_outline_missing_logline_triggers_repair(monkeypatch):
    monkeypatch.setattr("app.services.episode_agent.LANGGRAPH_AVAILABLE", True)
    monkeypatch.setattr("app.services.episode_agent.StateGraph", FakeGraph)
    monkeypatch.setattr("app.services.episode_agent.END", "END")

    outline_bad = {"episodes": [{"episode_number": 1, "title": "E1", "logline": ""}]}
    outline_fixed = {
        "episodes": [{"episode_number": 1, "title": "E1", "logline": "修复后"}]
    }
    episode = {
        "episodes": [
            {
                "episode_number": 1,
                "title": "E1",
                "summary": "S",
                "conflicts": [{"description": "c", "intensity": "low"}],
            }
        ]
    }

    ai_manager = FakeAIManager(
        [
            make_response(json.dumps(outline_bad)),
            make_response(json.dumps(outline_fixed)),  # repair
            make_response(json.dumps(episode)),
        ]
    )

    class Svc:
        def __init__(self):
            self.ai_manager = ai_manager

    agent = EpisodeLangGraphAgent(Svc())
    result = await agent.generate(
        story={"title": "T", "genre": "drama"},
        episode_count=1,
        episode_duration=None,
        focus_characters=None,
        plot_complexity="medium",
        pacing="medium",
        additional_requirements=None,
        style_preferences=None,
        model=None,
        prefer_provider=None,
        temperature=0.7,
    )

    assert result is not None
    assert result["normalized"]["episodes"][0]["summary"] == "S"
    assert result["step_outlines"]["episodes"][0]["logline"] == "修复后"
    assert "outline_too_short" in (result.get("reasoning") or [])
