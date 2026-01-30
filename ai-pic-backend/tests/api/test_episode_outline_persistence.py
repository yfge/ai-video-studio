import json

import pytest
from app.api.v1.endpoints.episodes import generation as episodes_generation
from app.models.script import Story
from app.models.story_structure import StoryStepOutline
from app.services import ai_service as ai_service_module


@pytest.mark.unit
def test_episode_generation_persists_validated_outlines(
    client, db_session, monkeypatch
):
    story = Story(title="故事", genre="drama")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    outlines = {
        "episodes": [
            {
                "episode_number": 1,
                "title": "Ep1",
                "logline": "一句话概要",
                "beats": [
                    {
                        "sequence_number": 1,
                        "beat_title": "开端",
                        "beat_summary": "主角登场",
                    }
                ],
            },
            {"episode_number": 2, "title": "Ep2", "logline": "第二集一句话"},
        ]
    }
    episodes_payload = {
        "episodes": [
            {
                "episode_number": 1,
                "title": "Ep1",
                "summary": "S1",
                "plot_points": [{"description": "P1"}],
                "character_arcs": {"hero": "grows"},
                "conflicts": [{"type": "x", "description": "c1"}],
            },
            {
                "episode_number": 2,
                "title": "Ep2",
                "summary": "S2",
                "plot_points": [{"description": "P2"}],
                "character_arcs": {"hero": "learns"},
                "conflicts": [{"type": "y", "description": "c2"}],
            },
        ]
    }

    class _StubAIService:
        async def generate_episodes(self, **_: str):
            return {
                "content": json.dumps(episodes_payload, ensure_ascii=False),
                "normalized": episodes_payload,
                "step_outlines": outlines,
                "step_outline_prompt": "outline prompt",
                "generation_method": "stub",
            }

    stub_service = _StubAIService()
    monkeypatch.setattr(ai_service_module, "ai_service", stub_service)
    monkeypatch.setattr(episodes_generation, "ai_service", stub_service)

    payload = {
        "story_id": story.id,
        "episode_count": 2,
        "episode_duration": 10,
        "plot_complexity": "simple",
        "pacing": "medium",
    }
    resp = client.post("/api/v1/episodes/generate", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 2

    db_session.refresh(story)
    meta = story.extra_metadata or {}
    outline_meta = meta.get("episode_step_outlines")
    assert outline_meta and outline_meta.get("episodes")
    assert outline_meta["episodes"][0]["logline"] == "一句话概要"

    rows = (
        db_session.query(StoryStepOutline)
        .filter(StoryStepOutline.story_id == story.id)
        .all()
    )
    assert len(rows) == 1
    assert rows[0].beat_title == "开端"


@pytest.mark.unit
def test_episode_generation_falls_back_to_outline_when_content_invalid(
    client, db_session, monkeypatch
):
    story = Story(title="Fallback 故事", genre="drama")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    outlines = {
        "episodes": [
            {"episode_number": 1, "title": "E1", "logline": "一句话1"},
            {"episode_number": 2, "title": "E2", "logline": "一句话2"},
        ]
    }

    class _StubAIService:
        async def generate_episodes(self, **_: str):
            return {
                "content": "Not JSON",
                "normalized": None,
                "step_outlines": outlines,
                "generation_method": "stub",
            }

    stub_service = _StubAIService()
    monkeypatch.setattr(ai_service_module, "ai_service", stub_service)
    monkeypatch.setattr(episodes_generation, "ai_service", stub_service)

    payload = {
        "story_id": story.id,
        "episode_count": 2,
        "episode_duration": 10,
        "plot_complexity": "simple",
        "pacing": "medium",
    }
    resp = client.post("/api/v1/episodes/generate", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 2
    assert body[0]["summary"] == "一句话1"
    assert body[1]["summary"] == "一句话2"
