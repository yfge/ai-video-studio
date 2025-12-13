import pytest

from app.schemas.style import ColorMood, CompositionStyle, StyleUniverse
from app.utils.style_utils import (
    DEFAULT_STYLE_SPEC,
    LEGACY_STYLE_PRESET_MAP,
    build_style_schema_options,
    build_style_prompt,
    derive_legacy_image_style,
    derive_openai_image_style,
    list_style_presets,
    resolve_style_spec,
)


def test_resolve_style_spec_defaults_to_platform_defaults():
    spec, meta = resolve_style_spec()

    assert spec.model_dump(mode="json") == DEFAULT_STYLE_SPEC.model_dump(mode="json")
    assert meta["preset_id"] is None
    assert meta["legacy_style"] is None
    assert meta["filled_defaults"] is True


def test_resolve_style_spec_preset_and_override_merges_correctly():
    spec, meta = resolve_style_spec(
        style_preset_id="cyberpunk_neon",
        style_spec={"color_mood": "monochrome"},
    )

    assert meta["preset_id"] == "cyberpunk_neon"
    assert spec.style_universe == StyleUniverse.CYBERPUNK
    assert spec.color_mood == ColorMood.MONOCHROME


def test_resolve_style_spec_legacy_style_maps_to_preset():
    spec, meta = resolve_style_spec(legacy_style="cartoon")

    assert meta["legacy_style"] == "cartoon"
    assert meta["preset_id"] == LEGACY_STYLE_PRESET_MAP["cartoon"]
    assert spec.style_universe == StyleUniverse.WESTERN_CARTOON


def test_build_style_prompt_contains_stable_labels():
    spec, _ = resolve_style_spec(style_preset_id="romance_anime_soft")
    prompt = build_style_prompt(spec)

    assert prompt.startswith("STYLE_SPEC => ")
    assert "style universe: japanese anime" in prompt
    assert "color mood: soft pastel" in prompt


def test_style_schema_options_use_chinese_labels():
    schema = build_style_schema_options()
    style_universe_labels = {opt.value: opt.label for opt in schema["style_universe"]}
    assert style_universe_labels["japanese_anime"] == "日系动漫"


def test_style_presets_expose_chinese_labels_and_descriptions():
    presets = {preset.preset_id: preset for preset in list_style_presets()}
    cyberpunk = presets["cyberpunk_neon"]
    assert cyberpunk.label == "赛博朋克·霓虹"
    assert cyberpunk.description and "赛博" in cyberpunk.description


def test_derive_legacy_image_style_portrait_focus():
    spec = DEFAULT_STYLE_SPEC.model_copy(
        update={"composition_style": CompositionStyle.PORTRAIT_FOCUS}
    )
    assert derive_legacy_image_style(spec) == "portrait"


@pytest.mark.parametrize(
    ("color_mood", "expected"),
    [
        (ColorMood.MONOCHROME, "natural"),
        (ColorMood.LOW_SATURATION, "natural"),
        (ColorMood.BRIGHT_VIVID, "vivid"),
        (ColorMood.HIGH_CONTRAST, "vivid"),
        (ColorMood.CINEMATIC_LUT, "vivid"),
    ],
)
def test_derive_openai_image_style_from_color_mood(color_mood, expected):
    spec = DEFAULT_STYLE_SPEC.model_copy(update={"color_mood": color_mood})
    assert derive_openai_image_style(spec, fallback="realistic") == expected
