import pytest
from app.services.story.story_generation_utils import (
    build_agent_run,
    build_extra_metadata,
)


@pytest.mark.unit
def test_build_extra_metadata_filters_excluded_fields() -> None:
    payload = {
        "premise": "p",
        "synopsis": "s",
        "main_conflict": "c",
        "resolution": "r",
        "main_characters": ["a"],
        "character_relationships": {"a": "b"},
        "custom": "ok",
    }

    result = build_extra_metadata(payload)

    assert result == {"custom": "ok"}


@pytest.mark.unit
def test_build_extra_metadata_handles_non_dict() -> None:
    assert build_extra_metadata(None) == {}


@pytest.mark.unit
def test_build_agent_run_extracts_expected_fields() -> None:
    payload = {
        "generation_method": "langgraph",
        "template_used": "template-a",
        "provider_used": "openai",
        "model_used": "gpt-4o-mini",
        "usage": {"total_tokens": 12},
        "reasoning": "ok",
        "extra": "ignored",
    }

    result = build_agent_run(payload)

    assert result == {
        "generation_method": "langgraph",
        "template_used": "template-a",
        "provider_used": "openai",
        "model_used": "gpt-4o-mini",
        "usage": {"total_tokens": 12},
        "reasoning": "ok",
    }


@pytest.mark.unit
def test_build_agent_run_handles_non_dict() -> None:
    assert build_agent_run("not-a-dict") == {}
