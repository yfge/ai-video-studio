import pytest
from app.services.providers.base import AIModelType, ProviderConfig
from app.services.providers.google_provider import GoogleProvider
from app.services.providers.google_provider import video as video_module


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

    async def post(self, url, json, headers=None):
        self.last_request = {"url": url, "json": json, "headers": headers}
        return _DummyResponse(200, self.payload)


@pytest.mark.asyncio
async def test_generate_video_uses_ratio_alias(monkeypatch):
    provider = GoogleProvider(ProviderConfig(name="google", api_key="test-key"))
    dummy_client = _DummyClient({"name": "operations/abc"})

    async def _fake_client():
        return dummy_client

    async def _fake_poll_operation(*_args, **_kwargs):
        return {
            "response": {
                "generateVideoResponse": {
                    "generatedSamples": [
                        {"video": {"uri": "https://example.com/video.mp4"}}
                    ]
                }
            }
        }

    monkeypatch.setattr(provider, "get_client", _fake_client)
    monkeypatch.setattr(video_module, "poll_veo_operation", _fake_poll_operation)

    resp = await provider.generate_video(
        prompt="test video",
        model="veo-3.1-generate-preview",
        resolution="720P",
        ratio="9:16",
        duration=4,
    )

    assert resp.success is True
    assert resp.model_type == AIModelType.TEXT_TO_VIDEO
    assert dummy_client.last_request is not None
    assert dummy_client.last_request["json"]["parameters"]["aspectRatio"] == "9:16"
