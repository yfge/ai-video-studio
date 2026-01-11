import pytest
from app.services.image_gen.refs import normalize_reference_images, resolve_base_image


@pytest.mark.unit
def test_resolve_base_image_rewrites_localhost_to_internal():
    assert (
        resolve_base_image(
            "http://localhost:8000/uploads/a.png",
            backend_base="http://ai-video-backend:8000",
        )
        == "http://ai-video-backend:8000/uploads/a.png"
    )


@pytest.mark.unit
def test_resolve_base_image_keeps_data_url():
    data_url = "data:image/png;base64,AAA"
    assert (
        resolve_base_image(data_url, backend_base="http://ai-video-backend:8000")
        == data_url
    )


@pytest.mark.unit
def test_normalize_reference_images_rewrites_localhost():
    refs = normalize_reference_images(
        ["http://127.0.0.1:8000/uploads/a.png"],
        backend_base="http://ai-video-backend:8000",
    )
    assert refs == ["http://ai-video-backend:8000/uploads/a.png"]
