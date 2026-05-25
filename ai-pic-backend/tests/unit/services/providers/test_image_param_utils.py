import pytest
from app.services.providers.image_param_utils import (
    compute_image_ui,
    normalize_image_params,
)


@pytest.mark.unit
def test_gpt_image_2_ui_sizes_include_high_resolution_options():
    rules = compute_image_ui("openai", "gpt-image-2")

    assert rules.size_options[:3] == ["1024x1024", "1536x1024", "1024x1536"]
    assert "3840x2160" in rules.size_options
    assert rules.supports_aspect_ratio is False


@pytest.mark.unit
def test_chatgpt_img_2_alias_uses_gpt_image_2_ui_sizes():
    rules = compute_image_ui("openai", "chatgpt-img-2")

    assert rules.size_options[:3] == ["1024x1024", "1536x1024", "1024x1536"]
    assert "3840x2160" in rules.size_options
    assert rules.supports_aspect_ratio is False


@pytest.mark.unit
def test_gpt_image_2_accepts_valid_custom_size():
    normalized_size, normalized_ratio, _ = normalize_image_params(
        "openai", "gpt-image-2", "1280x720", "16:9", strict=False
    )

    assert normalized_size == "1280x720"
    assert normalized_ratio is None


@pytest.mark.unit
def test_gpt_image_2_rejects_invalid_custom_size():
    normalized_size, _, _ = normalize_image_params(
        "openai", "gpt-image-2", "999x999", None, strict=False
    )

    assert normalized_size == "1024x1024"
