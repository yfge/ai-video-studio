from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.providers.volcengine_provider import image as volcengine_image


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


@pytest.mark.unit
@pytest.mark.asyncio
async def test_volcengine_generate_image_passes_guidance_scale_for_seedream3():
    client = MagicMock()
    client.post = AsyncMock(
        return_value=_DummyResponse({"data": [{"url": "http://example.com/img.png"}]})
    )

    response = await volcengine_image.generate_image(
        client=client,
        base_url="http://example.com/api/v3",
        provider_name="volcengine",
        prompt="test",
        model="doubao-seedream-3-0-t2i",
        cfg_scale=2.5,
    )

    assert response.success is True
    request_data = client.post.call_args.kwargs["json"]
    assert request_data["guidance_scale"] == 2.5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_volcengine_generate_image_omits_guidance_scale_for_seedream45():
    client = MagicMock()
    client.post = AsyncMock(
        return_value=_DummyResponse({"data": [{"url": "http://example.com/img.png"}]})
    )

    response = await volcengine_image.generate_image(
        client=client,
        base_url="http://example.com/api/v3",
        provider_name="volcengine",
        prompt="test",
        model="doubao-seedream-4-5-251128",
        cfg_scale=2.5,
    )

    assert response.success is True
    request_data = client.post.call_args.kwargs["json"]
    assert "guidance_scale" not in request_data
