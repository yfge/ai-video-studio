from app.services.ai.model_ui import ModelUiMixin


def _extract_image_gen(model: dict) -> dict:
    enriched = ModelUiMixin._apply_ui_metadata(dict(model))
    ui = enriched.get("metadata", {}).get("ui", {})
    assert "image_gen" in ui
    return ui["image_gen"]


def test_model_ui_image_gen_openai_has_no_negative_prompt():
    image_gen = _extract_image_gen(
        {
            "id": "dall-e-3",
            "type": "text_to_image",
            "provider": "openai",
            "capabilities": ["text_to_image"],
        }
    )

    assert image_gen["text_to_image"]["supports_negative_prompt"] is False
    assert image_gen["text_to_image"]["supports_steps"] is False
    assert image_gen["text_to_image"]["supports_cfg_scale"] is False
    assert image_gen["text_to_image"]["max_count"] == 1


def test_model_ui_image_gen_gpt_image_2_supports_reference_images():
    image_gen = _extract_image_gen(
        {
            "id": "gpt-image-2",
            "type": "text_to_image",
            "provider": "openai",
            "capabilities": ["text_to_image", "image_to_image"],
        }
    )

    assert image_gen["text_to_image"]["supports_negative_prompt"] is False
    assert image_gen["text_to_image"]["supports_reference_images"] is True
    assert image_gen["text_to_image"]["max_reference_images"] == 4
    assert image_gen["text_to_image"]["max_count"] == 4


def test_model_ui_image_gen_chatgpt_img_2_alias_supports_reference_images():
    image_gen = _extract_image_gen(
        {
            "id": "chatgpt-img-2",
            "type": "text_to_image",
            "provider": "openai",
            "capabilities": ["text_to_image", "image_to_image"],
        }
    )

    assert image_gen["text_to_image"]["supports_reference_images"] is True
    assert image_gen["text_to_image"]["max_reference_images"] == 4
    assert image_gen["text_to_image"]["max_count"] == 4


def test_model_ui_image_gen_jimeng_supports_steps_cfg_seed():
    image_gen = _extract_image_gen(
        {
            "id": "jimeng-sdxl",
            "type": "text_to_image",
            "provider": "jimeng",
            "capabilities": ["text_to_image"],
        }
    )

    assert image_gen["text_to_image"]["supports_seed"] is True
    assert image_gen["text_to_image"]["supports_steps"] is True
    assert image_gen["text_to_image"]["supports_cfg_scale"] is True
    assert image_gen["text_to_image"]["supports_negative_prompt"] is True

    assert image_gen["image_to_image"]["supports_strength"] is True
    assert image_gen["image_to_image"]["supports_negative_prompt"] is False


def test_model_ui_image_gen_keling_img2img_does_not_support_negative_prompt():
    image_gen = _extract_image_gen(
        {
            "id": "kling-v2",
            "type": "image_to_image",
            "provider": "keling",
            "capabilities": ["image_to_image"],
        }
    )

    assert image_gen["image_to_image"]["supports_negative_prompt"] is False
    assert image_gen["image_to_image"]["supports_image_fidelity"] is True
    assert image_gen["image_to_image"]["supports_human_fidelity"] is True
    assert any(
        "可灵图生图不支持 negative_prompt" in note
        for note in image_gen["image_to_image"].get("notes", [])
    )


def test_model_ui_image_gen_notes_are_mode_specific():
    image_gen = _extract_image_gen(
        {
            "id": "kling-v1",
            "type": "text_to_image",
            "provider": "keling",
            "capabilities": ["text_to_image", "image_to_image"],
        }
    )

    assert image_gen["text_to_image"]["supports_negative_prompt"] is True
    assert not any(
        "可灵图生图不支持 negative_prompt" in note
        for note in image_gen["text_to_image"].get("notes", [])
    )
    assert any(
        "可灵图生图不支持 negative_prompt" in note
        for note in image_gen["image_to_image"].get("notes", [])
    )


def test_model_ui_image_gen_volcengine_cfg_scale_model_specific():
    supported = _extract_image_gen(
        {
            "id": "seedream-3-0-t2i",
            "type": "text_to_image",
            "provider": "volcengine",
            "capabilities": ["text_to_image"],
        }
    )
    assert supported["text_to_image"]["supports_cfg_scale"] is True

    unsupported = _extract_image_gen(
        {
            "id": "seedream-4.5",
            "type": "text_to_image",
            "provider": "volcengine",
            "capabilities": ["text_to_image"],
        }
    )
    assert unsupported["text_to_image"]["supports_cfg_scale"] is False


def test_model_ui_image_gen_max_count_is_provider_aware():
    google = _extract_image_gen(
        {
            "id": "gemini-2.0-flash-exp",
            "type": "text_to_image",
            "provider": "google",
            "capabilities": ["text_to_image", "image_to_image"],
        }
    )
    assert google["text_to_image"]["max_count"] == 1
    assert google["image_to_image"]["max_count"] == 1

    volc = _extract_image_gen(
        {
            "id": "seedream-4.5",
            "type": "text_to_image",
            "provider": "volcengine",
            "capabilities": ["text_to_image", "image_to_image"],
        }
    )
    assert volc["text_to_image"]["max_count"] == 4
    assert volc["image_to_image"]["max_count"] == 4
