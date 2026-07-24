from types import SimpleNamespace

import pytest
from app.services.story import story_novel_task_processor as processor


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (None, "deepseek:deepseek-v4-flash"),
        ("codex:gpt-5.4", "codex:gpt-5.4"),
    ],
)
def test_structure_seed_uses_stable_planning_model(monkeypatch, configured, expected):
    captured = {}

    async def fake_structure(*args, **kwargs):
        captured["model"] = args[3].model

    monkeypatch.setattr(processor, "structure_story_seed", fake_structure)
    repo = SimpleNamespace(
        accessible_story=lambda business_id, user: SimpleNamespace(ai_model=configured)
    )

    processor._structure_seed(
        repo,
        db=None,
        task=None,
        payload={"story_business_id": "story-1", "story_seed_version": 1},
        user=object(),
    )

    assert captured["model"] == expected
