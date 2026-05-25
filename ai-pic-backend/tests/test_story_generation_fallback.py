import pytest
from app.core.logging import get_logger
from app.services.ai.story_outline import (
    StoryOutlineMixin,
    story_outline_fallback_generation_method,
)

_VALID_STORY_OUTLINE = """{
    "premise": "A compact fallback premise.",
    "synopsis": "A focused fallback synopsis.",
    "main_conflict": "The hero must choose between speed and craft.",
    "resolution": "The hero ships a smaller, reliable story.",
    "character_relationships": {"hero": "works with a trusted operator"},
    "main_characters": [
        {"name": "Hero", "role": "protagonist", "description": "Focused"}
    ]
}"""


class _FallbackStoryOutlineService(StoryOutlineMixin):
    def __init__(self, fallback_content: str):
        self.ai_manager = None
        self.story_agent = None
        self.fallback_content = fallback_content
        self.logger = get_logger()

    async def _call_text_generation_service(self, *args, **kwargs):
        return self.fallback_content


@pytest.mark.asyncio
async def test_story_outline_falls_back_to_mock_when_ai_manager_unavailable():
    service = _FallbackStoryOutlineService(_VALID_STORY_OUTLINE)

    result = await service.generate_story_outline(
        title="Fallback Story",
        genre="drama",
        characters=[{"name": "Hero", "description": "A curious hero"}],
        theme="fallback path",
    )

    assert result is not None
    assert result["generation_method"] == "ai_fallback"
    assert result["provider_used"] == "fallback"
    assert result.get("prompt")
    assert result.get("normalized")
    assert result["normalized"].get("premise")


@pytest.mark.asyncio
async def test_story_outline_marks_invalid_fallback_payload():
    service = _FallbackStoryOutlineService("not json")

    result = await service.generate_story_outline(
        title="Invalid Fallback Story",
        genre="drama",
        characters=[{"name": "Hero", "description": "A curious hero"}],
        theme="fallback path",
    )

    assert result is not None
    assert result["generation_method"] == "ai_fallback_invalid"
    assert result["provider_used"] == "fallback"
    assert result.get("prompt")
    assert result.get("normalized") is None
    assert result.get("validation_errors")


@pytest.mark.parametrize(
    ("normalized", "expected"),
    [
        ({"premise": "ok"}, "ai_fallback"),
        (None, "ai_fallback_invalid"),
        ({}, "ai_fallback_invalid"),
    ],
)
def test_story_outline_fallback_generation_method_names(normalized, expected):
    assert story_outline_fallback_generation_method(normalized) == expected
