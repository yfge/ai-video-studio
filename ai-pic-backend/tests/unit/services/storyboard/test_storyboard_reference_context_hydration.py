from __future__ import annotations

from app.models.story_structure import Environment, Scene
from app.services.storyboard.storyboard_audio_context_enricher import (
    enrich_storyboard_frames_with_story_context,
)
from tests.factories import (
    EpisodeFactory,
    ScriptFactory,
    StoryCharacterFactory,
    StoryFactory,
    VirtualIPFactory,
    setup_factories,
)


def test_audio_timeline_storyboard_enricher_matches_characters_from_shot_plan_text(
    db_session,
) -> None:
    setup_factories(db_session)

    story = StoryFactory()
    episode = EpisodeFactory(story=story)
    script = ScriptFactory(episode=episode)
    vip_a = VirtualIPFactory(
        name="林晚",
        default_avatar_url="http://example.com/lw.png",
        style_reference_images=[],
    )
    vip_b = VirtualIPFactory(
        name="陈哲",
        default_avatar_url="http://example.com/cz.png",
        style_reference_images=[],
    )
    StoryCharacterFactory(
        story=story,
        virtual_ip=vip_a,
        character_name="林晚",
        importance=5,
    )
    StoryCharacterFactory(
        story=story,
        virtual_ip=vip_b,
        character_name="陈哲",
        importance=4,
    )
    db_session.commit()

    frames = [
        {
            "frame_id": "f1",
            "frame_number": 1,
            "characters": [],
            "description": "林晚与陈哲隔着餐桌对视。",
            "prompt_description": "双人中景，冷色调。",
            "timeline_shot_plan": {
                "plot": "林晚与陈哲隔着餐桌对视。",
                "character_anchor": "林晚穿米色毛衣，陈哲穿深色夹克。",
            },
        }
    ]

    enrich_storyboard_frames_with_story_context(
        db_session,
        story_id=story.id,
        script_id=script.id,
        frames=frames,
        max_reference_images=3,
        max_character_cards=3,
    )

    assert frames[0]["characters"] == ["林晚", "陈哲"]
    assert frames[0]["reference_images"] == [
        "http://example.com/lw.png",
        "http://example.com/cz.png",
    ]


def test_reference_only_enrichment_uses_environment_without_character_visuals(
    db_session,
) -> None:
    setup_factories(db_session)

    story = StoryFactory()
    episode = EpisodeFactory(story=story)
    script = ScriptFactory(episode=episode)
    env = Environment(
        name="Empty Hallway",
        category="indoor",
        reference_images=["http://example.com/hallway.png"],
    )
    db_session.add(env)
    db_session.flush()
    scene = Scene(
        script_id=script.id,
        scene_number="1",
        slug_line="INT. HALLWAY - NIGHT",
        environment_id=env.id,
    )
    db_session.add(scene)
    db_session.commit()

    frames = [
        {
            "frame_id": "environment-only",
            "scene_id": int(scene.id),
            "scene_number": 1,
            "characters": [],
            "prompt_description": "Operator-authored environment prompt.",
        }
    ]

    enrich_storyboard_frames_with_story_context(
        db_session,
        story_id=story.id,
        script_id=script.id,
        frames=frames,
        max_reference_images=3,
        max_character_cards=3,
        update_prompt_context=False,
    )

    assert frames[0]["characters"] == []
    assert frames[0]["reference_images"] == ["http://example.com/hallway.png"]
    assert frames[0]["prompt_description"] == "Operator-authored environment prompt."


def test_reference_only_enrichment_does_not_infer_character_from_environment_prompt(
    db_session,
) -> None:
    setup_factories(db_session)

    story = StoryFactory()
    episode = EpisodeFactory(story=story)
    script = ScriptFactory(episode=episode)
    vip = VirtualIPFactory(
        name="老拐",
        default_avatar_url="http://example.com/laoguai.png",
        style_reference_images=[],
    )
    StoryCharacterFactory(
        story=story,
        virtual_ip=vip,
        character_name="老拐",
        importance=5,
    )
    db_session.commit()
    frames = [
        {
            "frame_id": "object-only",
            "description": "手机屏幕上快速滑过外卖图片。",
            "characters": [],
            "prompt_description": (
                "Object-only close-up. 环境锚点: 老拐的公寓厨房；"
                "保持环境光线和空间方向连续。"
            ),
            "ai_prompt": "Storyboard prompt using 老拐的公寓厨房 as environment.",
        }
    ]

    enrich_storyboard_frames_with_story_context(
        db_session,
        story_id=story.id,
        script_id=script.id,
        frames=frames,
        update_prompt_context=False,
    )

    assert frames[0]["characters"] == []
    assert not frames[0].get("reference_images")
