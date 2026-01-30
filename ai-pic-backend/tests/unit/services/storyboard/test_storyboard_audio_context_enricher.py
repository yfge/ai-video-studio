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


def test_audio_timeline_storyboard_enricher_injects_cards_and_reference_images(
    db_session,
) -> None:
    setup_factories(db_session)

    story = StoryFactory()
    episode = EpisodeFactory(story=story)
    script = ScriptFactory(episode=episode)

    vip_a = VirtualIPFactory(
        name="短剧女主-林晚-2026-01-30T00-00-00Z",
        description="25岁女性，黑长发，米色毛衣，白色短靴。",
        style_prompt="都市写实风格，米色针织衫，简洁妆容。",
        default_avatar_url="http://example.com/lw.png",
        style_reference_images=[],
    )
    vip_b = VirtualIPFactory(
        name="陈哲",
        description="30岁男性，短发，深色夹克。",
        style_prompt="都市写实风格，深色牛仔夹克。",
        default_avatar_url="http://example.com/cz.png",
        style_reference_images=[],
    )
    StoryCharacterFactory(
        story=story, virtual_ip=vip_a, character_name="林晚", importance=5
    )
    StoryCharacterFactory(
        story=story, virtual_ip=vip_b, character_name="陈哲", importance=4
    )

    env = Environment(
        name="公寓客厅",
        category="indoor",
        description="现代公寓客厅",
        reference_images=["http://example.com/env.png"],
    )
    db_session.add(env)
    db_session.flush()

    scene = Scene(
        script_id=script.id,
        scene_number="1",
        slug_line="INT. APARTMENT - NIGHT",
        location="上海",
        time_of_day="夜",
        environment_id=env.id,
    )
    db_session.add(scene)
    db_session.commit()

    frames = [
        {
            "frame_id": "f1",
            "frame_number": 1,
            "scene_id": int(scene.id),
            "scene_number": 1,
            "characters": ["林晚", "陈哲", "旁白"],
            "prompt_description": "林晚开口说话，嘴型清晰，真实口型；人物面容与服饰保持与参考图一致；无字幕，无可读文字。",
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
        "http://example.com/env.png",
    ]
    assert "开口说话" in frames[0]["prompt_description"]
    assert "角色卡:" in frames[0]["prompt_description"]
    assert "林晚" in frames[0]["prompt_description"]
    assert "陈哲" in frames[0]["prompt_description"]
    assert "环境锚点:" in frames[0]["prompt_description"]
    assert "公寓客厅" in frames[0]["prompt_description"]


def test_audio_timeline_storyboard_enricher_does_not_override_manual_reference_images(
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
    StoryCharacterFactory(story=story, virtual_ip=vip_a, character_name="林晚")

    frames = [
        {
            "frame_id": "f1",
            "frame_number": 1,
            "scene_id": 1,
            "scene_number": 1,
            "characters": ["林晚"],
            "prompt_description": "林晚开口说话，嘴型清晰。",
            "reference_images": ["http://example.com/manual.png"],
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

    assert frames[0]["reference_images"] == ["http://example.com/manual.png"]
    assert "角色卡:" in frames[0]["prompt_description"]

