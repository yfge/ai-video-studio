"""Tests for Codex reference-image file uploads."""

import httpx
import pytest
from app.services.providers.codex_image_references import (
    inline_reference_images,
    upload_codex_reference_files,
)


@pytest.mark.asyncio
async def test_custom_media_domain_uses_https_origin(monkeypatch):
    monkeypatch.setattr(
        "app.services.providers.codex_image_references.settings.ALIYUN_OSS_DOMAIN",
        "https://resource.example.com",
    )
    monkeypatch.setattr(
        "app.services.providers.codex_image_references.settings.ALIYUN_OSS_ENDPOINT",
        "https://oss-region.example.com",
    )
    monkeypatch.setattr(
        "app.services.providers.codex_image_references.settings.ALIYUN_OSS_BUCKET",
        "media-bucket",
    )

    prepared = await inline_reference_images(
        ["http://resource.example.com/images/reference.png?version=1"]
    )

    assert prepared == [
        "https://media-bucket.oss-region.example.com/images/reference.png?version=1"
    ]


@pytest.mark.asyncio
async def test_upload_codex_reference_files_uses_codex_file_protocol():
    calls = []

    async def handler(request):
        calls.append((request.method, str(request.url)))
        if request.method == "GET":
            return httpx.Response(
                200, content=b"png", headers={"content-type": "image/png"}
            )
        if request.url.path == "/backend-api/files":
            return httpx.Response(
                200,
                json={
                    "file_id": "file_123",
                    "upload_url": "https://blob.example/upload/reference",
                },
            )
        if request.method == "PUT":
            assert request.headers["x-ms-blob-type"] == "BlockBlob"
            assert await request.aread() == b"png"
            return httpx.Response(201)
        return httpx.Response(200, json={"status": "success"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        file_ids = await upload_codex_reference_files(
            ["https://resource.example/reference.png"],
            client=client,
            responses_url="https://chatgpt.com/backend-api/codex/responses",
            headers={"Authorization": "Bearer test"},
        )

    assert file_ids == ["file_123"]
    assert calls == [
        ("GET", "https://resource.example/reference.png"),
        ("POST", "https://chatgpt.com/backend-api/files"),
        ("PUT", "https://blob.example/upload/reference"),
        ("POST", "https://chatgpt.com/backend-api/files/file_123/uploaded"),
    ]
