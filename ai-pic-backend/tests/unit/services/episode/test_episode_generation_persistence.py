import pytest
from app.models.script import Story
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services.episode.episode_generation_persistence import create_episode_models


@pytest.mark.unit
def test_create_episode_models_persists_episode_summary_in_extra_metadata(db_session):
    story = Story(title="Test Story", genre="Drama", story_format="short_drama")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    request = EpisodeGenerationRequest(
        story_id=story.id, episode_count=1, episode_duration=10
    )
    episodes_data = [
        {
            "episode_number": 1,
            "title": "E1",
            "summary": "S1",
            "plot_points": [],
            "character_arcs": None,
            "conflicts": [{"description": "C1"}],
            "scene_count": 3,
        }
    ]

    created = create_episode_models(
        db=db_session,
        request=request,
        story=story,
        story_data={"title": story.title},
        episodes_data=episodes_data,
        result={},
        agent_run={},
        hook_plan_payload=None,
        ad_snippets_payload=None,
    )

    assert created
    assert created[0].extra_metadata
    assert created[0].extra_metadata["episode_summary"] == "S1"


@pytest.mark.unit
def test_create_episode_models_normalizes_underreported_scenes(db_session):
    story = Story(title="Test Story", genre="Drama", story_format="short_drama")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    request = EpisodeGenerationRequest(
        story_id=story.id, episode_count=1, episode_duration=10
    )
    episodes_data = [
        {
            "episode_number": 1,
            "title": "E1",
            "summary": "S1",
            "plot_points": [
                {"description": "hook", "timing": "开场"},
                {"description": "escalate", "timing": "中段"},
                {"description": "payoff", "timing": "后段"},
                {"description": "cliffhanger", "timing": "结尾"},
            ],
            "character_arcs": None,
            "conflicts": [{"description": "C1"}],
            "scene_count": 1,
            "scenes": [{"scene_number": 1, "summary": "hook"}],
        }
    ]

    created = create_episode_models(
        db=db_session,
        request=request,
        story=story,
        story_data={"title": story.title},
        episodes_data=episodes_data,
        result={},
        agent_run={},
        hook_plan_payload=None,
        ad_snippets_payload=None,
    )

    assert created[0].scene_count == 4
    scenes = created[0].extra_metadata["scenes"]
    assert [scene["scene_number"] for scene in scenes] == [1, 2, 3, 4]
