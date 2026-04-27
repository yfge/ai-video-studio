import pytest
from app.utils.model_utils import (
    DEFAULT_OPENAI_IMAGE_MODEL,
    is_gpt_image_model,
    is_openai_image_model,
    normalize_openai_image_style,
    parse_model_and_provider,
)


def test_parse_model_and_provider_splits_and_infers():
    model, provider = parse_model_and_provider("openai:dall-e-3")
    assert model == "dall-e-3"
    assert provider == "openai"

    model, provider = parse_model_and_provider("deepseek-chat")
    assert model == "deepseek-chat"
    assert provider == "deepseek"

    model, provider = parse_model_and_provider("openai:img-gen-2")
    assert model == DEFAULT_OPENAI_IMAGE_MODEL
    assert provider == "openai"

    model, provider = parse_model_and_provider("gpt-image-2")
    assert model == "gpt-image-2"
    assert provider == "openai"


def test_oai_image_model_detection():
    assert is_openai_image_model("gpt-image-2") is True
    assert is_openai_image_model("img-gen-2") is True
    assert is_openai_image_model("dall-e-3") is True
    assert is_gpt_image_model("gpt-image-2") is True
    assert is_gpt_image_model("dall-e-3") is False


@pytest.mark.parametrize(
    "style,expected",
    [
        ("natural", "natural"),
        ("vivid", "vivid"),
        (None, "natural"),
        ("", "natural"),
        ("realistic", "natural"),
        ("PhotoRealistic", "natural"),
        ("unknown-style", "natural"),
    ],
)
def test_normalize_openai_image_style(style, expected):
    assert normalize_openai_image_style(style) == expected
