from app.models.script import StoryCharacter
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.services.storyboard.clip_storyboard_context import (
    build_clip_storyboard_context,
)
from tests.fixtures.grid_storyboard_processor import (
    bootstrap_episode,
    create_timeline,
    timeline_spec,
)


def test_clip_storyboard_context_does_not_guess_between_multiple_characters(
    db_session,
):
    user, episode, script = bootstrap_episode(db_session)
    _add_story_character(db_session, episode.story_id, user.id, "林晚")
    _add_story_character(db_session, episode.story_id, user.id, "陈哲")
    timeline = create_timeline(
        db_session,
        episode,
        script,
        timeline_spec(episode, script),
        user,
    )

    result = build_clip_storyboard_context(
        db_session,
        timeline=timeline,
        clip={"clip_id": "clip-1", "track_type": "video", "text": "雨夜门口"},
        panels=[{"panel_id": "panel-1", "visual_prompt": "雨夜门口"}],
        request_reference_images=[],
    )

    assert result.bound_context["characters"] == []
    assert "character_context_not_resolved" in result.bound_context["warnings"]
    assert result.reference_images == []


def test_clip_storyboard_context_binds_single_story_character(db_session):
    user, episode, script = bootstrap_episode(db_session)
    virtual_ip = _add_story_character(db_session, episode.story_id, user.id, "林晚")
    timeline = create_timeline(
        db_session,
        episode,
        script,
        timeline_spec(episode, script),
        user,
    )

    result = build_clip_storyboard_context(
        db_session,
        timeline=timeline,
        clip={"clip_id": "clip-1", "track_type": "video", "text": "雨夜门口"},
        panels=[{"panel_id": "panel-1", "visual_prompt": "雨夜门口"}],
        request_reference_images=["https://manual.example/ref.png"],
    )

    assert result.bound_context["characters"] == [
        {
            "name": "林晚",
            "virtual_ip_id": virtual_ip.id,
            "appearance_brief": "林晚: 林晚 character profile",
            "anchor_url": "https://cdn.example/linwan.png",
        }
    ]
    assert result.reference_images == [
        "https://cdn.example/linwan.png",
        "https://manual.example/ref.png",
    ]
    assert result.bound_context["reference_bindings"] == [
        {
            "index": 1,
            "role": "character_identity",
            "label": "林晚",
            "source": "canonical_virtual_ip",
            "url": "https://cdn.example/linwan.png",
        },
        {
            "index": 2,
            "role": "general_reference",
            "label": "manual reference",
            "source": "request_reference_images",
            "url": "https://manual.example/ref.png",
        },
    ]
    assert result.panels[0]["bound_context"] == result.bound_context


def test_clip_storyboard_context_binds_speaker_alias_signal(db_session):
    user, episode, script = bootstrap_episode(db_session)
    _add_story_character(db_session, episode.story_id, user.id, "林晚")
    chen = _add_story_character(db_session, episode.story_id, user.id, "陈哲")
    spec = timeline_spec(episode, script)
    spec["tracks"].append(
        {
            "track_type": "dialogue",
            "clips": [
                {
                    "clip_id": "dialogue-1",
                    "scene_id": "scene_001",
                    "beat_id": "beat_001",
                    "speaker_name": "陈哲",
                    "text": "这一次我不会退。",
                }
            ],
        }
    )
    timeline = create_timeline(db_session, episode, script, spec, user)

    result = build_clip_storyboard_context(
        db_session,
        timeline=timeline,
        clip={
            "clip_id": "clip-1",
            "track_type": "video",
            "scene_id": "scene_001",
            "beat_id": "beat_001",
            "text": "车内侧脸",
        },
        panels=[{"panel_id": "panel-1", "visual_prompt": "车内侧脸"}],
        request_reference_images=[],
    )

    assert result.bound_context["characters"][0]["name"] == "陈哲"
    assert result.bound_context["characters"][0]["virtual_ip_id"] == chen.id
    assert result.reference_images == ["https://cdn.example/chenzhe.png"]


def _add_story_character(
    db_session, story_id: int, user_id: int, name: str
) -> VirtualIP:
    slug = "linwan" if name == "林晚" else "chenzhe"
    virtual_ip = VirtualIP(
        user_id=user_id,
        name=name,
        description=f"{name} character profile",
        style_prompt=f"{name} visual style",
    )
    db_session.add(virtual_ip)
    db_session.flush()
    db_session.add(
        VirtualIPImage(
            virtual_ip_id=virtual_ip.id,
            filename=f"{slug}.png",
            original_filename=f"{slug}.png",
            file_path=f"/uploads/{slug}.png",
            oss_url=f"https://cdn.example/{slug}.png",
            file_size=123,
            mime_type="image/png",
            category="avatar",
            is_default=True,
        )
    )
    db_session.add(
        StoryCharacter(
            story_id=story_id,
            virtual_ip_id=virtual_ip.id,
            character_name=name,
            role_type="protagonist",
            importance=5,
        )
    )
    db_session.commit()
    db_session.refresh(virtual_ip)
    return virtual_ip
