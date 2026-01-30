import pytest
from app.services.virtual_ip.image_variant_requests import (
    build_virtual_ip_variant_task_payload,
    resolve_virtual_ip_variant_request,
)


@pytest.mark.unit
def test_resolve_virtual_ip_variant_request_parses_img2img_advanced_params():
    req = resolve_virtual_ip_variant_request(
        {
            "prompt": "背面照",
            "model": "keling:kling-v1",
            "count": 2,
            "seed": 123,
            "steps": 30,
            "cfg_scale": 7.5,
            "strength": 0.66,
            "image_reference": "subject",
            "image_fidelity": 0.7,
            "human_fidelity": "0.5",
            "reference_images": ["http://example.com/ref.png"],
        },
        prompt=None,
        model=None,
        model_id=None,
        count=None,
        size=None,
        aspect_ratio=None,
        base_image_model="keling:kling-v1",
    )

    assert req.image_reference == "subject"
    assert req.image_fidelity == 0.7
    assert req.human_fidelity == 0.5


@pytest.mark.unit
def test_virtual_ip_variant_task_payload_includes_img2img_advanced_params():
    req = resolve_virtual_ip_variant_request(
        {
            "prompt": "背面照",
            "model": "keling:kling-v1",
            "image_reference": "subject",
            "image_fidelity": 0.7,
            "human_fidelity": 0.5,
        },
        prompt=None,
        model=None,
        model_id=None,
        count=None,
        size=None,
        aspect_ratio=None,
        base_image_model="keling:kling-v1",
    )
    payload = build_virtual_ip_variant_task_payload(
        virtual_ip_id=1,
        virtual_ip_business_id="virtual_ip_1",
        image_id=2,
        request=req,
    )

    assert payload["image_reference"] == "subject"
    assert payload["image_fidelity"] == 0.7
    assert payload["human_fidelity"] == 0.5
