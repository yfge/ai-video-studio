import pytest
from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)


@pytest.mark.unit
def test_keling_img2img_applies_profile_fidelity_defaults():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model="keling:kling-v2",
        base_image="/uploads/base.png",
        backend_base="http://localhost:8000",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.generation_profile == "balanced"
    assert normalized.image_fidelity == 0.5
    assert normalized.human_fidelity == 0.45
    assert normalized.audit.defaults_applied["image_fidelity"] == 0.5
    assert normalized.audit.defaults_applied["human_fidelity"] == 0.45


@pytest.mark.unit
def test_keling_img2img_call_includes_fidelity_params():
    req = ImageGenRequest(
        domain=ImageGenDomain.ENVIRONMENT,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model="keling:kling-v2",
        base_image="/uploads/base.png",
        backend_base="http://localhost:8000",
        generation_profile="identity",
    )
    normalized = normalize_image_gen_request(req)
    call = build_ai_manager_call(normalized)
    assert call["prefer_provider"] == "keling"
    assert call["image_fidelity"] == 0.7
    assert call["human_fidelity"] == 0.6
    assert "image_reference" not in call


@pytest.mark.unit
def test_keling_img2img_fidelity_clamped_to_unit_interval():
    req = ImageGenRequest(
        domain=ImageGenDomain.STORYBOARD,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model="keling:kling-v2",
        base_image="/uploads/base.png",
        backend_base="http://localhost:8000",
        image_fidelity=1.7,
        human_fidelity=-0.2,
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.image_fidelity == 1.0
    assert normalized.human_fidelity == 0.0
    assert any("image_fidelity > 1" in w for w in normalized.audit.warnings)
    assert any("human_fidelity < 0" in w for w in normalized.audit.warnings)


@pytest.mark.unit
def test_keling_v1_5_img2img_defaults_image_reference_subject():
    req = ImageGenRequest(
        domain=ImageGenDomain.VIRTUAL_IP,
        mode=ImageGenMode.IMAGE_TO_IMAGE,
        prompt="test",
        model="keling:kling-v1-5",
        base_image="/uploads/base.png",
        backend_base="http://localhost:8000",
    )
    normalized = normalize_image_gen_request(req)
    assert normalized.image_reference == "subject"
    assert normalized.audit.defaults_applied["image_reference"] == "subject"

    call = build_ai_manager_call(normalized)
    assert call["image_reference"] == "subject"
