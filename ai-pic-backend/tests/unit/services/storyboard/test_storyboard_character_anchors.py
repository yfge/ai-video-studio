from __future__ import annotations

import pytest

from app.models.script import Story, StoryCharacter
from app.models.virtual_ip import VirtualIP
from app.services.storyboard.storyboard_character_anchors import (
    extract_virtual_ip_name_aliases,
    fallback_virtual_ip_anchor_url,
    get_story_character_virtual_ip_ids,
    infer_character_ids_from_text,
)


@pytest.mark.unit
def test_get_story_character_virtual_ip_ids_orders_by_importance_and_dedup(db_session):
    vip_a = VirtualIP(user_id=1, name="A")
    vip_b = VirtualIP(user_id=1, name="B")
    db_session.add_all([vip_a, vip_b])
    db_session.commit()
    db_session.refresh(vip_a)
    db_session.refresh(vip_b)

    story = Story(
        user_id=1,
        title="S",
        story_format="short_drama",
        genre="drama",
        default_aspect_ratio="9:16",
    )
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    # B has higher importance and should be first; duplicates should be removed.
    db_session.add_all(
        [
            StoryCharacter(story_id=story.id, virtual_ip_id=vip_a.id, importance=1),
            StoryCharacter(story_id=story.id, virtual_ip_id=vip_b.id, importance=5),
            StoryCharacter(story_id=story.id, virtual_ip_id=vip_b.id, importance=2),
        ]
    )
    db_session.commit()

    assert get_story_character_virtual_ip_ids(db_session, story.id) == [
        vip_b.id,
        vip_a.id,
    ]


@pytest.mark.unit
def test_infer_character_ids_from_text_avoids_substring_overlaps():
    name_to_id = {"小雪": 19, "雪": 99}
    text = "小雪，你听我说，不是你想的那样……"
    assert infer_character_ids_from_text(text, name_to_id) == [19]


@pytest.mark.unit
def test_extract_virtual_ip_name_aliases_includes_human_name_segment():
    aliases = extract_virtual_ip_name_aliases(
        "短剧E2E女主-林雪-2026-01-19T03-52-25-958Z"
    )
    assert "林雪" in aliases


@pytest.mark.unit
def test_fallback_virtual_ip_anchor_url_prefers_default_avatar_then_style_refs():
    vip = VirtualIP(
        user_id=1,
        name="A",
        default_avatar_url="https://example.com/avatar.png",
        style_reference_images=["https://example.com/style-1.png"],
    )
    assert fallback_virtual_ip_anchor_url(vip) == "https://example.com/avatar.png"

    vip2 = VirtualIP(
        user_id=1,
        name="B",
        default_avatar_url=None,
        style_reference_images=["", "https://example.com/style-2.png"],
    )
    assert fallback_virtual_ip_anchor_url(vip2) == "https://example.com/style-2.png"

    vip3 = VirtualIP(user_id=1, name="C")
    assert fallback_virtual_ip_anchor_url(vip3) is None
