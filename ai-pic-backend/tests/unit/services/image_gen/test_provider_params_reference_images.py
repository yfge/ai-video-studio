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
