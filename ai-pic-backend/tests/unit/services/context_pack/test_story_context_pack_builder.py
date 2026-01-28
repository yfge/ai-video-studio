from __future__ import annotations

import pytest
from app.models.script import Episode, Story, StoryCharacter
from app.models.virtual_ip import VirtualIP
from app.schemas.context_pack import ContextPackBudget
from app.services.context_pack.story_context_pack_builder import (
    build_story_context_pack,
)


@pytest.mark.unit
def test_build_story_context_pack_includes_core_fields_and_trims(db_session) -> None:
    vip = VirtualIP(
        user_id=1,
        name="Alice",
        description="d" * 5000,
        background_story="b" * 5000,
        biography="bio" * 2000,
        style_prompt="style" * 2000,
        voice_config={"provider": "x", "voice_id": "y"},
    )
    db_session.add(vip)
    db_session.commit()
    db_session.refresh(vip)

    story = Story(
        user_id=1,
        title="S",
        story_format="short_drama",
        genre="drama",
        default_aspect_ratio="9:16",
        synopsis="syn" * 2000,
        main_conflict="conflict" * 2000,
        world_building="world" * 2000,
        character_relationships={"a_vs_b": "x" * 2000},
        generation_params={
            "style_preferences": ["neo-noir", "fast-cut"],
            "content_restrictions": ["no gore"],
        },
        extra_metadata={"continuity_ledger": {"big": "x" * 10000}},
    )
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    db_session.add(
        StoryCharacter(
            story_id=story.id,
            virtual_ip_id=vip.id,
            role_type="protagonist",
            importance=5,
        )
    )
    db_session.commit()

    ep1 = Episode(
        story_id=story.id,
        episode_number=1,
        title="E1",
        summary="summary 1",
        extra_metadata={"episode_summary": "ep_summary_1"},
    )
    ep2 = Episode(
        story_id=story.id,
        episode_number=2,
        title="E2",
        summary="summary 2",
        extra_metadata={},
    )
    db_session.add_all([ep1, ep2])
    db_session.commit()
    db_session.refresh(ep1)
    db_session.refresh(ep2)

    budget = ContextPackBudget(
        max_total_chars=1000,
        max_field_chars=200,
        max_character_cards=5,
        max_recent_episode_summaries=1,
    )
    snapshot = {
        "title": story.title,
        "story_format": story.story_format,
        "genre": story.genre,
        "default_aspect_ratio": story.default_aspect_ratio,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
        "world_building": story.world_building,
        "character_relationships": story.character_relationships,
        "market_region": "NA",
    }

    pack = build_story_context_pack(
        db=db_session,
        story_id=story.id,
        story_snapshot=snapshot,
        continuity_ledger=story.extra_metadata.get("continuity_ledger"),
        generation_params=story.generation_params,
        budget=budget,
    )

    assert pack["story_id"] == story.id
    assert pack["story_title"] == "S"
    assert pack["default_aspect_ratio"] == "9:16"
    assert pack["style_preferences"] == ["neo-noir", "fast-cut"]
    assert pack["content_restrictions"] == ["no gore"]

    assert pack["character_cards"]
    assert pack["character_cards"][0]["name"] == "Alice"
    assert pack["character_cards"][0]["role_type"] == "protagonist"
    assert pack["character_cards"][0]["biography"] is None  # dropped by budget

    assert len(pack["recent_episodes"]) == 1
    assert pack["recent_episodes"][0]["episode_number"] == 2
    assert pack["recent_episodes"][0]["summary"]  # falls back to Episode.summary

    assert pack["meta"]["budget"]["max_total_chars"] == 1000
    assert pack["meta"]["estimated_chars"] > 0
    assert pack["meta"]["trims"]  # at least one shrink action happened
