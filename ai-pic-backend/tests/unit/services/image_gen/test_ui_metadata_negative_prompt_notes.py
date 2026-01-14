import pytest
from app.services.image_gen.ui_metadata import build_image_gen_ui_metadata


@pytest.mark.unit
def test_ui_metadata_adds_negative_prompt_note_for_jimeng_img2img():
    meta = build_image_gen_ui_metadata(
        provider="jimeng", model_id="jimeng-img2img", caps=["image_to_image"]
    )
    notes = meta["image_gen"]["image_to_image"]["notes"]
    assert any("negative_prompt" in note for note in notes)


@pytest.mark.unit
def test_ui_metadata_does_not_add_note_when_jimeng_txt2img_supports_negative_prompt():
    meta = build_image_gen_ui_metadata(
        provider="jimeng", model_id="jimeng-sdxl", caps=["text_to_image"]
    )
    notes = meta["image_gen"]["text_to_image"]["notes"]
    assert not any("negative_prompt" in note for note in notes)


@pytest.mark.unit
def test_ui_metadata_uses_keling_specific_note_for_img2img():
    meta = build_image_gen_ui_metadata(
        provider="keling", model_id="kling-v2", caps=["image_to_image"]
    )
    notes = meta["image_gen"]["image_to_image"]["notes"]
    assert any("可灵图生图不支持 negative_prompt" in note for note in notes)
