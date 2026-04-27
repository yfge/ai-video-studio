from __future__ import annotations

import json

import pytest
from app.services.providers.base import AIModelType
from app.services.providers.volcengine_provider.models import (
    get_available_models,
    infer_model_type,
)
from app.services.providers.volcengine_provider.video_models import (
    SEEDANCE_20_FAST_MODEL,
    SEEDANCE_20_MODEL,
)
from app.services.providers.volcengine_provider.video_request import _normalize_model
from app.services.providers.volcengine_provider.video_tasks import submit_video_task


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.status_code = 200
        self.text = json.dumps(payload)

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class _Client:
    def __init__(self):
        self.posts: list[dict] = []

    async def post(self, _url: str, *, json: dict):
        self.posts.append(json)
        return _Response({"id": "cgt-test"})


def test_available_models_include_seedance_20():
    models = {model.model_id: model for model in get_available_models()}

    assert SEEDANCE_20_MODEL in models
    assert SEEDANCE_20_FAST_MODEL in models
    standard_ui = models[SEEDANCE_20_MODEL].metadata["ui"]
    fast_ui = models[SEEDANCE_20_FAST_MODEL].metadata["ui"]
    assert standard_ui["duration_options"][0] == 4
    assert standard_ui["duration_options"][-1] == 15
    assert standard_ui["supports_generate_audio"] is True
    assert standard_ui["supports_reference_video"] is True
    assert fast_ui["resolution_options"] == ["480P", "720P"]


def test_normalize_model_accepts_seedance_20_aliases():
    assert _normalize_model("seedance-2.0") == SEEDANCE_20_MODEL
    assert _normalize_model("seedance-2.0-i2v") == SEEDANCE_20_MODEL
    assert _normalize_model("seedance-2.0-fast") == SEEDANCE_20_FAST_MODEL
    assert _normalize_model("doubao-seedance-2-0-fast") == SEEDANCE_20_FAST_MODEL


def test_infer_model_type_treats_seedance_remote_models_as_video():
    assert (
        infer_model_type("doubao-seedance-2-0-260128", {}) == AIModelType.TEXT_TO_VIDEO
    )


@pytest.mark.asyncio
async def test_submit_seedance_20_uses_body_params_and_multimodal_refs():
    client = _Client()

    response = await submit_video_task(
        client=client,
        base_url="https://ark.example.com/api/v3",
        provider_name="volcengine",
        prompt="小猫看向镜头",
        image_url=None,
        model="seedance-2.0",
        duration=15,
        fps=60,
        resolution="1920x1080",
        end_image_url=None,
        ratio="adaptive",
        watermark=False,
        seed=11,
        camera_fixed=True,
        service_tier="default",
        execution_expires_after=3600,
        return_last_frame=True,
        reference_images=["https://cdn.example.com/ref.png"],
        reference_videos=["https://cdn.example.com/ref.mp4"],
        reference_audios=["https://cdn.example.com/ref.wav"],
        generate_audio=False,
        tools=[{"type": "web_search"}],
        safety_identifier="user-hash",
    )

    payload = client.posts[-1]
    roles = [item.get("role") for item in payload["content"]]
    assert response.success is True
    assert response.model == SEEDANCE_20_MODEL
    assert response.model_type == AIModelType.IMAGE_TO_VIDEO
    assert payload["model"] == SEEDANCE_20_MODEL
    assert payload["duration"] == 15
    assert payload["resolution"] == "1080p"
    assert payload["ratio"] == "adaptive"
    assert payload["generate_audio"] is False
    assert payload["watermark"] is False
    assert payload["seed"] == 11
    assert "camera_fixed" not in payload
    assert "fps" not in payload
    assert roles == [
        None,
        "reference_image",
        "reference_video",
        "reference_audio",
    ]


@pytest.mark.asyncio
async def test_submit_seedance_20_first_last_frame_skips_refs():
    client = _Client()

    await submit_video_task(
        client=client,
        base_url="https://ark.example.com/api/v3",
        provider_name="volcengine",
        prompt="镜头推进",
        image_url="https://cdn.example.com/start.png",
        model=SEEDANCE_20_MODEL,
        duration=4,
        fps=24,
        resolution="720p",
        end_image_url="https://cdn.example.com/end.png",
        ratio="16:9",
        watermark=None,
        seed=None,
        camera_fixed=None,
        service_tier=None,
        execution_expires_after=None,
        return_last_frame=None,
        reference_images=["https://cdn.example.com/ref.png"],
    )

    roles = [item.get("role") for item in client.posts[-1]["content"]]
    assert roles == [None, "first_frame", "last_frame"]


@pytest.mark.asyncio
async def test_submit_seedance_20_fast_downgrades_1080p_and_skips_flex():
    client = _Client()

    await submit_video_task(
        client=client,
        base_url="https://ark.example.com/api/v3",
        provider_name="volcengine",
        prompt="城市夜景",
        image_url=None,
        model="seedance-2.0-fast",
        duration=20,
        fps=24,
        resolution="1080p",
        end_image_url=None,
        ratio=None,
        watermark=None,
        seed=None,
        camera_fixed=True,
        service_tier="flex",
        execution_expires_after=None,
        return_last_frame=None,
    )

    payload = client.posts[-1]
    assert payload["model"] == SEEDANCE_20_FAST_MODEL
    assert payload["resolution"] == "720p"
    assert payload["duration"] == 15
    assert "service_tier" not in payload
    assert "camera_fixed" not in payload
