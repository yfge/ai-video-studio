import pytest
from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)


@pytest.mark.unit
def test_environment_policy_disables_style_spec():
    req = ImageGenRequest(
        domain=ImageGenDomain.ENVIRONMENT,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="seedream-4.5",
        style="realistic",
        style_preset_id="preset",
        style_spec={"style_universe": "japanese_anime"},
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.style_preset_id is None
    assert normalized.style_spec is None


@pytest.mark.unit
def test_parse_provider_prefix_and_infer_provider():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="keling:kling-image-v2",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.provider == "keling"
    assert normalized.model_id == "kling-image-v2"


@pytest.mark.unit
def test_openai_drops_aspect_ratio_and_defaults_size_on_invalid():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="openai:dall-e-3",
        size="999x999",
        aspect_ratio="16:9",
    )
    normalized = normalize_image_gen_request(req)
    # OpenAI DALL-E does not support aspect_ratio in our UI rules
    assert normalized.aspect_ratio is None
    # Invalid size should fall back to default for that model (1024x1024)
    assert normalized.size == "1024x1024"


@pytest.mark.unit
def test_reference_images_normalization_requires_backend_base():
    req = ImageGenRequest(
        domain=ImageGenDomain.STORYBOARD,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model="volcengine:seedream-4.5",
        base_image="/uploads/a.png",
        reference_images=["uploads/b.png", "not-a-url", "http://example.com/c.jpg"],
    )
    normalized = normalize_image_gen_request(req, strict=False)
    assert normalized.extra_images == []
    assert any("backend_base is missing" in w for w in normalized.audit.warnings)


@pytest.mark.unit
def test_reference_images_normalized_and_base_image_resolved():
    req = ImageGenRequest(
        domain=ImageGenDomain.STORYBOARD,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model="volcengine:seedream-4.5",
        base_image="uploads/a.png",
        reference_images=["uploads/b.png", "not-a-url", "http://example.com/c.jpg"],
        backend_base="http://localhost:8000",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.base_image_url == "http://localhost:8000/uploads/a.png"
    assert normalized.extra_images == [
        "http://localhost:8000/uploads/b.png",
        "http://example.com/c.jpg",
    ]


@pytest.mark.unit
def test_build_ai_manager_call_filters_jimeng_aspect_ratio():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="jimeng:jimeng-sdxl",
        size="1024x1024",
        aspect_ratio="16:9",
    )
    normalized = normalize_image_gen_request(req)
    call = build_ai_manager_call(normalized)
    assert call["prefer_provider"] == "jimeng"
    assert "aspect_ratio" not in call


@pytest.mark.unit
def test_build_ai_manager_call_keeps_extra_images_without_provider():
    req = ImageGenRequest(
        domain=ImageGenDomain.ENVIRONMENT,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model=None,
        base_image="/uploads/base.png",
        reference_images=["/uploads/ref.png"],
        backend_base="http://localhost:8000",
    )
    normalized = normalize_image_gen_request(req)
    call = build_ai_manager_call(normalized)
    assert call["extra_images"] == ["http://localhost:8000/uploads/ref.png"]


@pytest.mark.unit
def test_profile_defaults_applied_for_jimeng():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="jimeng:jimeng-sdxl",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.generation_profile == "balanced"
    assert normalized.steps == 30
    assert normalized.cfg_scale == 7.0
    assert normalized.negative_prompt
    assert normalized.audit.defaults_applied["generation_profile"] == "balanced"
    assert normalized.audit.defaults_applied["steps"] == 30
    assert normalized.audit.defaults_applied["cfg_scale"] == 7.0


@pytest.mark.unit
def test_profile_quality_for_jimeng():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="jimeng:jimeng-sdxl",
        generation_profile="quality",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.generation_profile == "quality"
    assert normalized.steps == 40
    assert normalized.cfg_scale == 7.5
    assert "generation_profile" not in normalized.audit.defaults_applied


@pytest.mark.unit
def test_profile_unknown_falls_back_to_default():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="jimeng:jimeng-sdxl",
        generation_profile="does-not-exist",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.generation_profile == "balanced"
    assert any("unknown generation_profile" in w for w in normalized.audit.warnings)


@pytest.mark.unit
def test_profile_fallback_when_invalid_steps():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="jimeng:jimeng-sdxl",
        generation_profile="quality",
        steps=0,
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.generation_profile == "quality"
    assert normalized.steps == 40
    assert any("invalid steps" in w for w in normalized.audit.warnings)


@pytest.mark.unit
def test_profile_negative_prompt_appends_virtual_ip_overlay():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="jimeng:jimeng-sdxl",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.negative_prompt
    assert "multiple faces" in normalized.negative_prompt.lower()
    assert normalized.audit.defaults_applied.get("negative_prompt_virtual_ip")


@pytest.mark.unit
def test_profile_negative_prompt_storyboard_has_no_multi_face_term():
    req = ImageGenRequest(
        domain=ImageGenDomain.STORYBOARD,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="jimeng:jimeng-sdxl",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.negative_prompt
    assert "multiple faces" not in normalized.negative_prompt.lower()


@pytest.mark.unit
def test_user_negative_prompt_not_modified_by_virtual_ip_overlay():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="jimeng:jimeng-sdxl",
        negative_prompt="user override",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.negative_prompt == "user override"
    assert "negative_prompt" not in normalized.audit.defaults_applied


@pytest.mark.unit
def test_profile_strength_default_applied_for_jimeng_img2img():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model="jimeng:jimeng-img2img",
        base_image="http://example.com/base.png",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.generation_profile == "balanced"
    assert normalized.strength == 0.75
    assert normalized.audit.defaults_applied.get("strength") == 0.75


@pytest.mark.unit
def test_profile_defaults_applied_for_volcengine_seedream3_text_to_image():
    req = ImageGenRequest(
        domain=ImageGenDomain.ENVIRONMENT,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="volcengine:doubao-seedream-3-0-t2i",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.generation_profile == "balanced"
    assert normalized.cfg_scale == 2.5
    assert normalized.audit.defaults_applied.get("cfg_scale") == 2.5

    call = build_ai_manager_call(normalized)
    assert call.get("cfg_scale") == 2.5


@pytest.mark.unit
def test_profile_defaults_applied_for_volcengine_seededit3_img2img():
    req = ImageGenRequest(
        domain=ImageGenDomain.ENVIRONMENT,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model="volcengine:doubao-seededit-3-0-i2i",
        base_image="http://example.com/base.png",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.generation_profile == "balanced"
    assert normalized.cfg_scale == 5.5
    assert normalized.audit.defaults_applied.get("cfg_scale") == 5.5

    call = build_ai_manager_call(normalized)
    assert call.get("cfg_scale") == 5.5
