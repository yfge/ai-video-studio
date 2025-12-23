import pytest

from app.services.providers.base import AIModelType, ProviderConfig
from app.services.providers.google_provider import GoogleProvider


class _DummyResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.request = None

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"status {self.status_code}")


class _DummyClient:
    def __init__(self, payload: dict):
        self.payload = payload
        self.last_request = None

    async def post(self, url, json):
        self.last_request = {"url": url, "json": json}
        return _DummyResponse(200, self.payload)


@pytest.mark.asyncio
async def test_generate_image_success(monkeypatch):
    provider = GoogleProvider(ProviderConfig(name="google", api_key="test-key"))
    dummy_client = _DummyClient(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": "AAAABBBB",
                                }
                            }
                        ]
                    }
                }
            ]
        }
    )
    async def _fake_client():
        return dummy_client
    monkeypatch.setattr(provider, "get_client", _fake_client)

    resp = await provider.generate_image(
        prompt="sunset over mountains",
        model="gemini-2.0-flash-exp",
        response_modalities=["IMAGE"],
        aspect_ratio="16:9",
    )

    assert resp.success is True
    assert resp.model_type == AIModelType.TEXT_TO_IMAGE
    assert resp.data and resp.data["images"]
    assert resp.data["images"][0].startswith("data:image/png;base64,")
    assert "sunset" in dummy_client.last_request["json"]["contents"][0]["parts"][0]["text"]
    # 验证 responseModalities 字段已正确设置
    assert "generationConfig" in dummy_client.last_request["json"]
    assert "responseModalities" in dummy_client.last_request["json"]["generationConfig"]
    assert dummy_client.last_request["json"]["generationConfig"]["responseModalities"] == ["IMAGE"]
    assert dummy_client.last_request["json"]["generationConfig"]["imageConfig"]["aspectRatio"] == "16:9"


@pytest.mark.asyncio
async def test_generate_image_strips_provider_prefix(monkeypatch):
    """测试模型名称中的 provider 前缀被正确清理"""
    provider = GoogleProvider(ProviderConfig(name="google", api_key="test-key"))
    dummy_client = _DummyClient(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": "TESTDATA",
                                }
                            }
                        ]
                    }
                }
            ]
        }
    )
    async def _fake_client():
        return dummy_client
    monkeypatch.setattr(provider, "get_client", _fake_client)

    # 使用带有 provider 前缀的模型名称
    resp = await provider.generate_image(prompt="test image", model="google:gemini-3-pro-image-preview")

    assert resp.success is True
    # 验证 URL 中的模型名称不包含 provider 前缀
    assert "google:gemini-3-pro-image-preview" not in dummy_client.last_request["url"]
    assert "gemini-3-pro-image-preview" in dummy_client.last_request["url"]


@pytest.mark.asyncio
async def test_image_to_image_uses_reference(monkeypatch):
    provider = GoogleProvider(ProviderConfig(name="google", api_key="test-key"))
    dummy_client = _DummyClient(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": "CCCCDDDD",
                                }
                            }
                        ]
                    }
                }
            ]
        }
    )
    async def _fake_client():
        return dummy_client
    monkeypatch.setattr(provider, "get_client", _fake_client)

    resp = await provider.image_to_image(
        image_url="http://example.com/img.png",
        prompt="make it dramatic",
        model="gemini-2.0-flash-exp",
        base64_images=["data:image/png;base64,REFIMG"],
    )

    assert resp.success is True
    assert resp.model_type == AIModelType.IMAGE_TO_IMAGE
    assert resp.data and resp.data["images"]
    parts = dummy_client.last_request["json"]["contents"][0]["parts"]
    assert any("text" in p and "dramatic" in p["text"] for p in parts)
    assert any("inlineData" in p for p in parts)
    # 验证 responseModalities 字段已正确设置
    assert "generationConfig" in dummy_client.last_request["json"]
    assert "responseModalities" in dummy_client.last_request["json"]["generationConfig"]
    assert dummy_client.last_request["json"]["generationConfig"]["responseModalities"] == ["TEXT", "IMAGE"]
