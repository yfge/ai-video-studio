import pytest
from app.services.image_gen.ui_metadata import build_image_gen_ui_metadata


@pytest.mark.unit
def test_ui_metadata_txt2img_reference_images_false_for_openai_even_with_img2img_cap():
    meta = build_image_gen_ui_metadata(
        provider="openai", model_id="dall-e-3", caps=["text_to_image", "image_to_image"]
    )
    assert meta["image_gen"]["text_to_image"]["supports_reference_images"] is False


@pytest.mark.unit
def test_ui_metadata_txt2img_reference_images_true_for_google():
    meta = build_image_gen_ui_metadata(
        provider="google",
        model_id="gemini-2.0-flash-image-exp",
        caps=["text_to_image"],
    )
    assert meta["image_gen"]["text_to_image"]["supports_reference_images"] is True
    assert meta["image_gen"]["text_to_image"].get("max_reference_images") == 4


@pytest.mark.unit
def test_ui_metadata_txt2img_reference_images_true_for_keling():
    meta = build_image_gen_ui_metadata(
        provider="keling",
        model_id="kling-v2-1",
        caps=["text_to_image"],
    )
    assert meta["image_gen"]["text_to_image"]["supports_reference_images"] is True
    assert meta["image_gen"]["text_to_image"].get("max_reference_images") == 1
