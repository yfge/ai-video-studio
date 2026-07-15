from app.services.storyboard.clip_storyboard_context import (
    build_clip_storyboard_context,
)
from tests.fixtures.clip_storyboard_characters import (
    add_episode_character,
    add_story_character,
)
from tests.fixtures.grid_storyboard_processor import (
    bootstrap_episode,
    create_timeline,
    timeline_spec,
)


def test_clip_storyboard_context_binds_episode_character_ip(db_session):
    user, episode, script = bootstrap_episode(db_session)
    temporary = add_episode_character(
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
            "appearance_brief": "快递员: 快递员 character profile",
            "anchor_url": "https://cdn.example/courier.png",
        }
    ]
    assert result.reference_images == ["https://cdn.example/courier.png"]


def test_clip_storyboard_context_prefers_explicit_ip_over_text_match(db_session):
    user, episode, script = bootstrap_episode(db_session)
    add_story_character(db_session, episode.story_id, user.id, "林晚")
    courier = add_episode_character(db_session, episode.id, user.id, "快递员")
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
            "appearance_brief": "快递员: 快递员 character profile",
            "anchor_url": "https://cdn.example/courier.png",
        }
    ]
    assert result.reference_images == ["https://cdn.example/courier.png"]


def test_clip_storyboard_context_prefers_request_ip_selection(db_session):
    user, episode, script = bootstrap_episode(db_session)
    add_story_character(db_session, episode.story_id, user.id, "林晚")
    courier = add_episode_character(db_session, episode.id, user.id, "快递员")
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
            "appearance_brief": "快递员: 快递员 character profile",
            "anchor_url": "https://cdn.example/courier.png",
        }
    ]
    assert result.reference_images == ["https://cdn.example/courier.png"]


def test_clip_storyboard_context_prioritizes_canonical_selected_ip_anchor(
    db_session,
):
    user, episode, script = bootstrap_episode(db_session)
    courier = add_episode_character(db_session, episode.id, user.id, "快递员")
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
        request_reference_images=[
            "https://selected.example/ip.png",
            "https://manual.example/ref.png",
        ],
        request_character_virtual_ip_ids=[courier.id],
        request_character_reference_images=["https://selected.example/ip.png"],
        request_environment_reference_images=["https://selected.example/env.png"],
    )

    assert result.reference_images == [
        "https://cdn.example/courier.png",
        "https://selected.example/env.png",
        "https://manual.example/ref.png",
    ]
    assert (
        "noncanonical_character_references_ignored" in result.bound_context["warnings"]
    )
    assert result.bound_context["reference_bindings"] == [
        {
            "index": 1,
            "role": "character_identity",
            "label": "快递员",
            "source": "canonical_virtual_ip",
            "url": "https://cdn.example/courier.png",
        },
        {
            "index": 2,
            "role": "environment",
            "label": "requested environment",
            "source": "request_environment_reference_images",
            "url": "https://selected.example/env.png",
        },
        {
            "index": 3,
            "role": "general_reference",
            "label": "manual reference",
            "source": "request_reference_images",
            "url": "https://manual.example/ref.png",
        },
    ]
