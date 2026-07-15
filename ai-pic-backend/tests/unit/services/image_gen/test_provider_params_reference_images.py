import pytest
from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "model",
    [
        "google:gemini-2.5-flash-image",
        "volcengine:seedream-4.5",
    ],
)
def test_build_ai_manager_call_passes_reference_images_for_text_to_image(model: str):
    req = ImageGenRequest(
        domain=ImageGenDomain.STORYBOARD,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model=model,
        reference_images=["/uploads/ref.png"],
        backend_base="http://localhost:8000",
    )
    normalized = normalize_image_gen_request(req)
    call = build_ai_manager_call(normalized)
    assert call["reference_images"] == ["http://localhost:8000/uploads/ref.png"]


@pytest.mark.unit
def test_build_ai_manager_call_maps_reference_images_to_keling_image_param():
    req = ImageGenRequest(
        domain=ImageGenDomain.STORYBOARD,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="test",
        model="keling:kling-v2-1",
        reference_images=["/uploads/ref.png"],
        backend_base="http://localhost:8000",
    )
    normalized = normalize_image_gen_request(req)
    call = build_ai_manager_call(normalized)
    assert call["image"] == "http://localhost:8000/uploads/ref.png"
    assert "reference_images" not in call


@pytest.mark.unit
def test_build_ai_manager_call_keeps_codex_style_for_audit():
    req = ImageGenRequest(
        domain=ImageGenDomain.STORYBOARD,
        mode=ImageGenMode.TEXT_TO_IMAGE,
        prompt="four-panel storyboard",
        model="codex:gpt-image-2",
        style="3d_cartoon",
    )

    call = build_ai_manager_call(normalize_image_gen_request(req))

    assert call["prefer_provider"] == "codex"
    assert call["style"] == "3d_cartoon"
