import aiohttp
import pytest
from app.services.render.video_download import download_video


class _FakeResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def read(self):
        return b"video"


class _RetrySession:
    def __init__(self):
        self.calls = 0

    def get(self, _url):
        self.calls += 1
        if self.calls == 1:
            return _DisconnectingResponse()
        return _FakeResponse()


class _DisconnectingResponse:
    async def __aenter__(self):
        raise aiohttp.ServerDisconnectedError()

    async def __aexit__(self, *_args):
        return None


@pytest.mark.asyncio
async def test_download_video_retries_disconnected_server():
    session = _RetrySession()

    payload = await download_video(
        "https://example.com/video.mp4",
        session,
        retries=2,
        retry_delay_seconds=0,
    )

    assert payload == b"video"
    assert session.calls == 2
