import pytest

from app.utils.model_utils import (
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
