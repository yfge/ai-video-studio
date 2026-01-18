import pytest

from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    normalize_image_gen_request,
)


@pytest.mark.unit
def test_openai_drops_unsupported_sampling_params():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="openai:dall-e-3",
        seed=123,
        steps=30,
        cfg_scale=7.0,
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.seed is None
    assert normalized.steps is None
    assert normalized.cfg_scale is None
    assert any("seed ignored" in w for w in normalized.audit.warnings)
    assert any("steps ignored" in w for w in normalized.audit.warnings)
    assert any("cfg_scale ignored" in w for w in normalized.audit.warnings)


@pytest.mark.unit
def test_volcengine_cfg_scale_dropped_when_model_does_not_support_guidance_scale():
    req = ImageGenRequest(
        domain=ImageGenDomain.ENVIRONMENT,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="volcengine:seedream-4.5",
        cfg_scale=7.0,
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.cfg_scale is None
    assert any("cfg_scale ignored" in w for w in normalized.audit.warnings)


@pytest.mark.unit
def test_keling_img2img_drops_strength_when_unsupported():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model="keling:kling-v2",
        base_image="/uploads/base.png",
        backend_base="http://localhost:8000",
        strength=0.85,
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.strength is None
    assert any("strength ignored" in w for w in normalized.audit.warnings)


@pytest.mark.unit
def test_openai_drops_style_spec_when_unsupported():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="openai:dall-e-3",
        style_spec={"style_universe": "japanese_anime"},
        style_preset_id="anime",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.style_spec is None
    assert normalized.style_preset_id is None
    assert any("style_spec ignored" in w for w in normalized.audit.warnings)
    assert any("style_preset_id ignored" in w for w in normalized.audit.warnings)

