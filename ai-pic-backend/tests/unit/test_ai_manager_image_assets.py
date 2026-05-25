from types import SimpleNamespace

import pytest
from app.services import ai_manager_image_assets as image_assets


def test_prefer_http_for_download_rewrites_https():
    assert image_assets.prefer_http_for_download("https://example.com/a.png") == (
        "http://example.com/a.png"
    )
    assert image_assets.prefer_http_for_download("http://example.com/a.png") == (
        "http://example.com/a.png"
    )


def test_maybe_compress_inline_image_returns_small_payload():
    content, content_type = image_assets.maybe_compress_inline_image(
        b"abc",
        content_type="image/png",
        target_max_bytes=100,
        max_side=512,
    )

    assert content == b"abc"
    assert content_type == "image/png"


@pytest.mark.asyncio
async def test_preload_image_references_as_data_urls(monkeypatch):
    import httpx

    calls: list[str] = []
    client_kwargs: dict[str, object] = {}

    class _Response:
        headers = {"Content-Type": "image/png"}
        content = b"abc"

        def raise_for_status(self):
            return None

    class _Client:
        def __init__(self, **kwargs):
            client_kwargs.update(kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url):
            calls.append(url)
            return _Response()

    monkeypatch.setattr(httpx, "AsyncClient", _Client)
    logger = SimpleNamespace(warning=lambda *_args, **_kwargs: None)

    result = await image_assets.preload_image_references_as_data_urls(
        image_url="https://example.com/ref.png",
        extra_images=[],
        prefer_provider="openai",
        available_providers=["openai"],
        timeout=12.0,
        logger=logger,
    )

    assert calls == ["http://example.com/ref.png"]
    assert client_kwargs["timeout"] == 12.0
    assert result == ["data:image/png;base64,YWJj"]
