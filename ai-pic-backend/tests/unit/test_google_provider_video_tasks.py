import pytest

from app.services.providers.google_provider import GoogleProvider
from app.services.providers.google_provider import video_tasks as video_tasks_module
from app.services.providers.base import ProviderConfig


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
    def __init__(self, *, post_payload: dict | None = None, get_payload: dict | None = None):
        self.post_payload = post_payload or {}
        self.get_payload = get_payload or {}
        self.last_post = None
        self.last_get = None

    async def post(self, url, json):
        self.last_post = {"url": url, "json": json}
        return _DummyResponse(200, self.post_payload)

    async def get(self, url):
        self.last_get = {"url": url}
        return _DummyResponse(200, self.get_payload)


@pytest.mark.asyncio
async def test_submit_video_task_returns_task_id(monkeypatch):
    provider = GoogleProvider(ProviderConfig(name="google", api_key="test-key"))
    dummy_client = _DummyClient(post_payload={"name": "operations/abc"})

    async def _fake_client():
        return dummy_client

    async def _fake_fetch_image_bytes(*_args, **_kwargs):
        return {"mimeType": "image/png", "bytesBase64Encoded": "AAA"}

    monkeypatch.setattr(provider, "get_client", _fake_client)
    monkeypatch.setattr(video_tasks_module, "fetch_image_bytes", _fake_fetch_image_bytes)

    resp = await provider.submit_video_task(
        prompt="test video",
        image_url="https://example.com/start.png",
        model="veo-3.1-generate-preview",
        duration=4,
        resolution="720P",
        ratio="9:16",
    )

    assert resp.success is True
    assert (resp.data or {}).get("task_id") == "operations/abc"
    assert dummy_client.last_post is not None
    assert (
        dummy_client.last_post["json"]["instances"][0]["image"]["bytesBase64Encoded"]
        == "AAA"
    )
    assert dummy_client.last_post["json"]["parameters"]["aspectRatio"] == "9:16"


@pytest.mark.asyncio
async def test_fetch_video_task_status_success_extracts_video_url(monkeypatch):
    provider = GoogleProvider(ProviderConfig(name="google", api_key="test-key"))
    dummy_client = _DummyClient(
        get_payload={
            "done": True,
            "response": {
                "generateVideoResponse": {
                    "generatedSamples": [{"video": {"uri": "https://example.com/video.mp4"}}]
                }
            },
        }
    )

    async def _fake_client():
        return dummy_client

    monkeypatch.setattr(provider, "get_client", _fake_client)

    resp = await provider.fetch_video_task_status("operations/abc")

    assert resp.success is True
    assert (resp.data or {}).get("status") == "success"
    assert (resp.data or {}).get("video_url") == "https://example.com/video.mp4"
    assert (resp.data or {}).get("download_url") == "https://example.com/video.mp4?key=test-key"
    assert dummy_client.last_get is not None
    assert dummy_client.last_get["url"].endswith("/v1beta/operations/abc")


@pytest.mark.asyncio
async def test_fetch_video_task_status_failed_maps_error(monkeypatch):
    provider = GoogleProvider(ProviderConfig(name="google", api_key="test-key"))
    dummy_client = _DummyClient(get_payload={"done": True, "error": {"message": "boom"}})

    async def _fake_client():
        return dummy_client

    monkeypatch.setattr(provider, "get_client", _fake_client)

    resp = await provider.fetch_video_task_status("operations/abc")

    assert resp.success is True
    assert (resp.data or {}).get("status") == "failed"
    assert (resp.data or {}).get("error") == "boom"
