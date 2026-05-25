from app.services import ai_manager_image_style as image_style
from app.services.providers.base import AIModelType, AIResponse, AITaskType


def test_resolve_text_to_image_style_injects_prompt_and_openai_style():
    state = image_style.resolve_text_to_image_style(
        prompt="A test prompt",
        legacy_style="realistic",
        style_preset_id="cyberpunk_neon",
        style_spec={"color_mood": "monochrome"},
    )

    assert "STYLE_SPEC =>" in state.prompt
    assert state.legacy_style == "realistic"
    assert state.openai_style_override == "natural"
    assert state.resolved_style_spec is not None
    assert state.resolution_meta is not None
    assert state.resolution_meta["preset_id"] == "cyberpunk_neon"


def test_resolve_image_to_image_style_handles_empty_prompt():
    state = image_style.resolve_image_to_image_style(
        prompt=None,
        legacy_style="cartoon",
        style_preset_id="romance_anime_soft",
        style_spec=None,
    )

    assert state.prompt is not None
    assert "STYLE_SPEC =>" in state.prompt
    assert state.legacy_style == "portrait"
    assert state.resolved_style_spec is not None


def test_attach_style_metadata_noops_without_resolved_spec():
    response = AIResponse(
        success=True,
        data={},
        provider="openai",
        model="gpt-image-1",
        task_type=AITaskType.PORTRAIT_GENERATION,
        model_type=AIModelType.TEXT_TO_IMAGE,
        metadata={"existing": "value"},
    )

    image_style.attach_style_metadata(response, None, {"error": "ignored"})

    assert response.metadata == {"existing": "value"}
