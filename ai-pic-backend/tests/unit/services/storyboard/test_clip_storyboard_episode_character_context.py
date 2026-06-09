from app.models.episode_character import EpisodeCharacter
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


def test_clip_storyboard_context_binds_episode_character_ip(db_session):
    user, episode, script = bootstrap_episode(db_session)
    temporary = _add_episode_character(
        db_session,
        episode.id,
        user.id,
        "快递员",
    )
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
        clip={
            "clip_id": "clip-1",
            "track_type": "video",
            "source_refs": {"virtual_ip_id": temporary.id},
            "text": "快递员把包裹递进门。",
        },
        panels=[{"panel_id": "panel-1", "visual_prompt": "快递员递包裹"}],
        request_reference_images=[],
    )

    assert result.bound_context["characters"] == [
        {
            "name": "快递员",
            "virtual_ip_id": temporary.id,
            "anchor_url": "https://cdn.example/courier.png",
        }
    ]
    assert result.reference_images == ["https://cdn.example/courier.png"]


def test_clip_storyboard_context_prefers_explicit_ip_over_text_match(db_session):
    user, episode, script = bootstrap_episode(db_session)
    _add_story_character(db_session, episode.story_id, user.id, "林晚")
    courier = _add_episode_character(db_session, episode.id, user.id, "快递员")
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
        clip={
            "clip_id": "clip-1",
            "track_type": "video",
            "virtual_ip_id": courier.id,
            "text": "林晚看着快递员递来的包裹。",
        },
        panels=[{"panel_id": "panel-1", "visual_prompt": "林晚看向快递员"}],
        request_reference_images=[],
    )

    assert result.bound_context["characters"] == [
        {
            "name": "快递员",
            "virtual_ip_id": courier.id,
            "anchor_url": "https://cdn.example/courier.png",
        }
    ]
    assert result.reference_images == ["https://cdn.example/courier.png"]


def test_clip_storyboard_context_prefers_request_ip_selection(db_session):
    user, episode, script = bootstrap_episode(db_session)
    _add_story_character(db_session, episode.story_id, user.id, "林晚")
    courier = _add_episode_character(db_session, episode.id, user.id, "快递员")
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
        clip={
            "clip_id": "clip-1",
            "track_type": "video",
            "text": "林晚打开门，接过快递员递来的包裹。",
        },
        panels=[{"panel_id": "panel-1", "visual_prompt": "林晚接过包裹"}],
        request_reference_images=[],
        request_character_virtual_ip_ids=[courier.id],
    )

    assert result.bound_context["characters"] == [
        {
            "name": "快递员",
            "virtual_ip_id": courier.id,
            "anchor_url": "https://cdn.example/courier.png",
        }
    ]
    assert result.reference_images == ["https://cdn.example/courier.png"]


def test_clip_storyboard_context_prioritizes_selected_reference_images(
    db_session,
):
    user, episode, script = bootstrap_episode(db_session)
    courier = _add_episode_character(db_session, episode.id, user.id, "快递员")
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
        clip={
            "clip_id": "clip-1",
            "track_type": "video",
            "text": "快递员把包裹递进门。",
        },
        panels=[{"panel_id": "panel-1", "visual_prompt": "快递员递包裹"}],
        request_reference_images=["https://manual.example/ref.png"],
        request_character_virtual_ip_ids=[courier.id],
        request_character_reference_images=["https://selected.example/ip.png"],
        request_environment_reference_images=["https://selected.example/env.png"],
    )

    assert result.reference_images == [
        "https://selected.example/ip.png",
        "https://selected.example/env.png",
        "https://manual.example/ref.png",
        "https://cdn.example/courier.png",
    ]


def _add_story_character(
    db_session, story_id: int, user_id: int, name: str
) -> VirtualIP:
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
            filename="linwan.png",
            original_filename="linwan.png",
            file_path="/uploads/linwan.png",
            oss_url="https://cdn.example/linwan.png",
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


def _add_episode_character(
    db_session,
    episode_id: int,
    user_id: int,
    name: str,
) -> VirtualIP:
    slug = "courier" if name == "快递员" else name
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
        EpisodeCharacter(
            episode_id=episode_id,
            virtual_ip_id=virtual_ip.id,
            character_name=name,
            role_type="temporary",
            importance=3,
        )
    )
    db_session.commit()
    db_session.refresh(virtual_ip)
    return virtual_ip
