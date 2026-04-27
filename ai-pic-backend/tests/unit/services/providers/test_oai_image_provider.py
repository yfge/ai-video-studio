from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.providers.openai_provider import image


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_image_uses_gpt_image_2_payload():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"data": [{"b64_json": "base64imagedata"}]}
    client.post.return_value = response

    result = await image.generate_image(
        client=client,
        base_url="https://api.openai.com/v1",
        provider_name="openai",
        prompt="draw a cat" * 500,
        model="img-gen-2",
        size="2048x1152",
    )

    assert result.success is True
    assert result.model == "gpt-image-2"
    assert result.data["images"] == ["data:image/png;base64,base64imagedata"]

    payload = client.post.call_args.kwargs["json"]
    assert payload["model"] == "gpt-image-2"
    assert payload["size"] == "2048x1152"
    assert payload["quality"] == "auto"
    assert "style" not in payload
    assert "response_format" not in payload
    assert len(payload["prompt"]) > 1000


@pytest.mark.unit
@pytest.mark.asyncio
async def test_image_to_image_gpt_image_2_uses_edits_endpoint():
    client = AsyncMock()
    get_response = MagicMock()
    get_response.raise_for_status = MagicMock()
    get_response.content = b"image-bytes"
    get_response.headers = {"Content-Type": "image/png"}
    client.get.return_value = get_response

    post_response = MagicMock()
    post_response.raise_for_status = MagicMock()
    post_response.json.return_value = {"data": [{"b64_json": "edited"}]}
    form_client = AsyncMock()
    form_client.post.return_value = post_response

    with patch("app.services.providers.openai_provider.image.httpx.AsyncClient") as cls:
        cls.return_value.__aenter__.return_value = form_client

        result = await image.image_to_image(
            client=client,
            base_url="https://api.openai.com/v1",
            provider_name="openai",
            api_key="test-api-key",
            config_timeout=60,
            image_url="https://example.com/ref.png",
            prompt="make it cinematic",
            model="gpt-image-2",
            size="1024x1024",
        )

    assert result.success is True
    assert result.data["images"] == ["data:image/png;base64,edited"]

    assert (
        form_client.post.call_args.args[0] == "https://api.openai.com/v1/images/edits"
    )
    kwargs = form_client.post.call_args.kwargs
    assert kwargs["data"]["model"] == "gpt-image-2"
    assert kwargs["data"]["prompt"] == "make it cinematic"
    assert kwargs["files"][0][0] == "image[]"
