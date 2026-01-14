import pytest

from app.services.story_structure.environment_image_requests import (
    build_environment_variant_task_payload,
    resolve_environment_image_variant_request,
)


@pytest.mark.unit
def test_resolve_environment_image_variant_request_parses_img2img_advanced_params():
    req = resolve_environment_image_variant_request(
        {
            "base_image": "http://example.com/base.png",
            "prompt": "保持同一空间风格，生成细节变化",
            "model": "keling:kling-v1",
            "image_reference": "subject",
            "image_fidelity": 0.7,
            "human_fidelity": "0.5",
        },
        base_image=None,
        fallback_base_image=None,
        prompt=None,
        model=None,
        count=None,
        size=None,
        aspect_ratio=None,
    )

    assert req.image_reference == "subject"
    assert req.image_fidelity == 0.7
    assert req.human_fidelity == 0.5


@pytest.mark.unit
def test_environment_variant_task_payload_includes_img2img_advanced_params():
    req = resolve_environment_image_variant_request(
        {
            "base_image": "http://example.com/base.png",
            "image_reference": "subject",
            "image_fidelity": 0.7,
            "human_fidelity": 0.5,
        },
        base_image=None,
        fallback_base_image=None,
        prompt=None,
        model=None,
        count=None,
        size=None,
        aspect_ratio=None,
    )
    payload = build_environment_variant_task_payload(env_id=1, request=req)

    assert payload["image_reference"] == "subject"
    assert payload["image_fidelity"] == 0.7
    assert payload["human_fidelity"] == 0.5

