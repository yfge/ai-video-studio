import pytest

from app.services.image_gen.ui_metadata import build_image_gen_ui_metadata


@pytest.mark.unit
def test_ui_metadata_reports_style_spec_support_for_keling():
    meta = build_image_gen_ui_metadata(
        provider="keling", model_id="kling-v2", caps=["text_to_image", "image_to_image"]
    )

    t2i = meta["image_gen"]["text_to_image"]
    assert t2i["supports_style_preset_id"] is True
    assert t2i["supports_style_spec"] is True

    i2i = meta["image_gen"]["image_to_image"]
    assert i2i["supports_style_preset_id"] is True
    assert i2i["supports_style_spec"] is True
    assert i2i["supports_extra_images"] is False


@pytest.mark.unit
def test_ui_metadata_reports_no_style_spec_support_for_google():
    meta = build_image_gen_ui_metadata(
        provider="google",
        model_id="gemini-2.0-flash-image",
        caps=["text_to_image", "image_to_image"],
    )

    t2i = meta["image_gen"]["text_to_image"]
    assert t2i["supports_style_preset_id"] is False
    assert t2i["supports_style_spec"] is False

    i2i = meta["image_gen"]["image_to_image"]
    assert i2i["supports_style_preset_id"] is False
    assert i2i["supports_style_spec"] is False
    assert i2i["supports_extra_images"] is True
