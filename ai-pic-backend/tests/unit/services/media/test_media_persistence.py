import base64
import hashlib

import pytest

from app.services.media.media_persistence import (
    build_generation_metadata,
    upload_base64,
    upload_from_url,
)


class _FakeOSS:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    async def upload_from_url(self, **kwargs):
        self.calls.append(("upload_from_url", kwargs))
        return {"success": True, "file_url": "https://cdn.example.com/file"}

    async def upload_file_content(self, **kwargs):
        self.calls.append(("upload_file_content", kwargs))
        return {"success": True, "file_url": "https://cdn.example.com/file"}


def test_build_generation_metadata_filters_non_ascii():
    meta = build_generation_metadata(
        provider="google",
        model="veo",
        media_type="video",
        extra={"prompt": "中文", "ok": "ascii"},
    )
    assert meta["provider"] == "google"
    assert meta["media_type"] == "video"
    assert meta["ok"] == "ascii"
    assert "prompt" not in meta


@pytest.mark.asyncio
async def test_upload_from_url_normalizes_and_filters_metadata():
    fake = _FakeOSS()
    url = "https://example.com/file?foo=bar baz"
    result = await upload_from_url(
        url=url,
        media_type="video",
        metadata={"prompt": "中文", "ok": "ascii"},
        oss_service_override=fake,
    )
    assert result and result["success"] is True
    assert fake.calls
    name, kwargs = fake.calls[0]
    assert name == "upload_from_url"
    assert kwargs["url"] == "https://example.com/file?foo=bar%20baz"
    assert kwargs["metadata"] == {"ok": "ascii"}


@pytest.mark.asyncio
async def test_upload_base64_adds_sha256():
    fake = _FakeOSS()
    content = b"hello"
    payload = base64.b64encode(content).decode("ascii")
    expected = hashlib.sha256(content).hexdigest()

    await upload_base64(
        base64_payload=payload,
        filename="file.mp4",
        media_type="video",
        metadata={"ok": "ascii"},
        oss_service_override=fake,
    )

    assert fake.calls
    name, kwargs = fake.calls[0]
    assert name == "upload_file_content"
    assert kwargs["metadata"]["ok"] == "ascii"
    assert kwargs["metadata"]["sha256"] == expected

