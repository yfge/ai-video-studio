from __future__ import annotations

import pytest

from app.services.narrative_context import extract_story_characters


@pytest.mark.unit
def test_extract_story_characters_prefers_characters() -> None:
    story = {
        "characters": [{"name": "主角"}, {"name": "主角"}, {"character_name": "反派"}],
        "character_profiles": [{"name": "备用"}],
        "main_characters": [{"name": "旧角色"}],
    }

    assert extract_story_characters(story) == [
        {"name": "主角"},
        {"character_name": "反派", "name": "反派"},
    ]


@pytest.mark.unit
def test_extract_story_characters_supports_character_profiles() -> None:
    story = {"character_profiles": [{"character_name": "林雪", "role": "lead"}]}

    assert extract_story_characters(story) == [
        {"character_name": "林雪", "role": "lead", "name": "林雪"}
    ]


@pytest.mark.unit
def test_extract_story_characters_supports_main_characters_strings() -> None:
    story = {"main_characters": ["陈哲", {"name": "林雪"}]}

    assert extract_story_characters(story) == [{"name": "陈哲"}, {"name": "林雪"}]
