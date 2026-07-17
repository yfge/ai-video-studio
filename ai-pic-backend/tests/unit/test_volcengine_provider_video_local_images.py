from __future__ import annotations

import base64
import io
import json

import pytest
from app.services.providers.volcengine_provider import video_image_inputs
from app.services.providers.volcengine_provider.video import generate_video
from app.services.providers.volcengine_provider.video_tasks import submit_video_task
from PIL import Image


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload
        self.content = json.dumps(payload).encode()

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class _Client:
    def __init__(self):
        self.posts: list[dict] = []

    async def post(self, _url: str, *, json: dict):
        self.posts.append(json)
        return _Response({"id": "cgt-local-image"})


def _jpeg_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(output, format="JPEG")
    return output.getvalue()


def _write_mislabeled_jpeg(path) -> None:
    path.write_bytes(_jpeg_bytes())


async def _submit(client: _Client, **overrides):
    values = {
        "client": client,
        "base_url": "https://ark.example.com/api/v3",
        "provider_name": "volcengine",
        "prompt": "镜头推进",
        "image_url": None,
        "model": "seedance-2.0",
        "duration": 4,
        "fps": 24,
        "resolution": "720p",
        "end_image_url": None,
        "ratio": None,
        "watermark": None,
        "seed": None,
        "camera_fixed": None,
        "service_tier": None,
        "execution_expires_after": None,
        "return_last_frame": None,
    }
    values.update(overrides)
    return await submit_video_task(**values)


def _assert_failed_without_provider(response, client: _Client, message: str) -> None:
    assert response.success is False
    assert message in (response.error or "")
    assert client.posts == []


@pytest.mark.asyncio
async def test_local_first_and_end_frames_use_sniffed_mime(tmp_path, monkeypatch):
    monkeypatch.setattr(video_image_inputs.settings, "UPLOAD_DIR", str(tmp_path))
    _write_mislabeled_jpeg(tmp_path / "first.png")
    _write_mislabeled_jpeg(tmp_path / "last.png")
    client = _Client()
    response = await _submit(
        client,
        image_url="http://localhost:8000/uploads/first.png",
        end_image_url="http://ai-video-backend:8000/uploads/last.png",
    )
    urls = [item["image_url"]["url"] for item in client.posts[0]["content"][:2]]
    assert response.success is True
    assert all(url.startswith("data:image/jpeg;base64,") for url in urls)


@pytest.mark.asyncio
async def test_generate_fails_when_any_local_reference_is_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(video_image_inputs.settings, "UPLOAD_DIR", str(tmp_path))
    _write_mislabeled_jpeg(tmp_path / "local.png")
    client = _Client()

    async def fake_poll(*_args, **_kwargs):
        return {
            "status": "succeeded",
            "content": {"video_url": "https://cdn.example.com/out.mp4"},
        }

    monkeypatch.setattr(
        "app.services.providers.volcengine_provider.video.poll_task_status",
        fake_poll,
    )
    response = await generate_video(
        client=client,
        base_url="https://ark.example.com/api/v3",
        provider_name="volcengine",
        prompt="连续镜头",
        model="seedance-2.0",
        duration=4,
        fps=24,
        resolution="720p",
        reference_images=[
            "/uploads/local.png",
            "/uploads/missing.png",
            "https://cdn.example.com/public.png",
        ],
    )
    _assert_failed_without_provider(
        response,
        client,
        "reference_images[2] local image cannot be read",
    )


@pytest.mark.asyncio
async def test_missing_reference_image_urls_fail_before_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(video_image_inputs.settings, "UPLOAD_DIR", str(tmp_path))
    client = _Client()
    response = await _submit(
        client,
        reference_image_urls=[
            "http://127.0.0.1:8000/uploads/missing.png",
            "/uploads/also-missing.png",
        ],
    )
    _assert_failed_without_provider(
        response,
        client,
        "reference_image_urls[1] local image cannot be read",
    )


@pytest.mark.asyncio
async def test_submit_inlines_local_reference_image_urls(tmp_path, monkeypatch):
    monkeypatch.setattr(video_image_inputs.settings, "UPLOAD_DIR", str(tmp_path))
    _write_mislabeled_jpeg(tmp_path / "reference.png")
    client = _Client()
    response = await _submit(
        client,
        reference_image_urls=["/uploads/reference.png"],
    )
    sent = client.posts[0]["content"][1]["image_url"]["url"]
    assert response.success is True
    assert sent.startswith("data:image/jpeg;base64,")


@pytest.mark.asyncio
async def test_bad_image_fails_even_with_reference_video(tmp_path, monkeypatch):
    monkeypatch.setattr(video_image_inputs.settings, "UPLOAD_DIR", str(tmp_path))
    client = _Client()
    response = await _submit(
        client,
        reference_images=["/uploads/missing.png"],
        reference_videos=["https://cdn.example.com/reference.mp4"],
    )
    _assert_failed_without_provider(
        response,
        client,
        "reference_images[1] local image cannot be read",
    )


@pytest.mark.asyncio
async def test_invalid_local_image_fails_before_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(video_image_inputs.settings, "UPLOAD_DIR", str(tmp_path))
    (tmp_path / "invalid.png").write_bytes(b"not an image")
    client = _Client()
    response = await _submit(
        client,
        reference_images=["/uploads/invalid.png"],
    )
    _assert_failed_without_provider(response, client, "is not a valid image")


@pytest.mark.asyncio
async def test_invalid_data_reference_image_fails_before_provider():
    client = _Client()
    response = await _submit(
        client,
        reference_images=["data:image/png;base64,aGVsbG8="],
    )
    _assert_failed_without_provider(response, client, "is not a valid image: data URL")


@pytest.mark.asyncio
async def test_missing_required_local_frame_fails_before_provider(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(video_image_inputs.settings, "UPLOAD_DIR", str(tmp_path))
    client = _Client()
    response = await _submit(client, image_url="/uploads/missing.png")
    _assert_failed_without_provider(
        response,
        client,
        "image_url local image cannot be read",
    )


@pytest.mark.asyncio
async def test_submit_inlines_configured_internal_backend_host(tmp_path, monkeypatch):
    monkeypatch.setattr(video_image_inputs.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(
        video_image_inputs.settings,
        "INTERNAL_BACKEND_URL",
        "http://custom-video-backend:8000",
    )
    _write_mislabeled_jpeg(tmp_path / "frame.png")
    client = _Client()
    response = await _submit(
        client,
        image_url="http://custom-video-backend:8000/uploads/frame.png",
    )
    sent = client.posts[0]["content"][0]["image_url"]["url"]
    assert response.success is True
    assert sent.startswith("data:image/jpeg;base64,")


@pytest.mark.asyncio
async def test_submit_ignores_bad_refs_for_model_without_reference_media():
    client = _Client()
    response = await _submit(
        client,
        model="doubao-seedance-1-5-pro-251215",
        reference_images=["/uploads/missing.png"],
    )
    assert response.success is True
    assert [item["type"] for item in client.posts[0]["content"]] == ["text"]


@pytest.mark.asyncio
async def test_submit_enforces_single_and_total_inline_image_limits(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(video_image_inputs.settings, "UPLOAD_DIR", str(tmp_path))
    _write_mislabeled_jpeg(tmp_path / "first.png")
    _write_mislabeled_jpeg(tmp_path / "last.png")
    client = _Client()
    monkeypatch.setattr(video_image_inputs, "MAX_SINGLE_IMAGE_BYTES", 100)
    single = await _submit(client, image_url="/uploads/first.png")
    _assert_failed_without_provider(single, client, "smaller than 100 bytes")

    monkeypatch.setattr(video_image_inputs, "MAX_SINGLE_IMAGE_BYTES", 10_000)
    monkeypatch.setattr(video_image_inputs, "MAX_TOTAL_INLINE_IMAGE_BYTES", 1_000)
    total = await _submit(
        client,
        image_url="/uploads/first.png",
        end_image_url="/uploads/last.png",
    )
    _assert_failed_without_provider(
        total,
        client,
        "inline image total must be smaller than 1000 bytes",
    )

    data_url = "data:image/jpeg;base64," + base64.b64encode(_jpeg_bytes()).decode()
    monkeypatch.setattr(video_image_inputs, "MAX_SINGLE_IMAGE_BYTES", 100)
    oversized_data = await _submit(client, reference_images=[data_url])
    _assert_failed_without_provider(
        oversized_data,
        client,
        "reference_images[1] image must be smaller than 100 bytes",
    )


@pytest.mark.asyncio
async def test_submit_preserves_public_data_and_asset_references():
    client = _Client()
    data_url = "data:image/jpeg;base64," + base64.b64encode(_jpeg_bytes()).decode()
    references = [
        "https://cdn.example.com/ref.png",
        data_url,
        "asset://media/42",
    ]
    response = await _submit(client, reference_images=references)
    sent = [
        item["image_url"]["url"]
        for item in client.posts[0]["content"]
        if item.get("role") == "reference_image"
    ]
    assert response.success is True
    assert sent == references
