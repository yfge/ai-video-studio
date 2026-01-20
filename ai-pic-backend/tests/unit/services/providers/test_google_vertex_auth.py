import time
from unittest.mock import MagicMock

import pytest

from app.services.providers.google_provider import vertex_auth as vertex_auth_module


def test_build_vertex_access_token_provider_from_json():
    provider = vertex_auth_module.build_vertex_access_token_provider(
        service_account_json='{"client_email":"svc@example.com","private_key":"key"}',
        service_account_path=None,
        logger=MagicMock(),
    )
    assert provider is not None


@pytest.mark.asyncio
async def test_vertex_access_token_provider_caches_and_refreshes(monkeypatch):
    info = {
        "client_email": "svc@example.com",
        "private_key": "key",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    monkeypatch.setattr(
        vertex_auth_module,
        "build_service_account_assertion",
        lambda **_: "assertion",
    )
    calls = []

    async def _fake_request_access_token(*, token_uri: str, assertion: str, timeout: float = 10.0):
        calls.append((token_uri, assertion))
        return {"access_token": f"token{len(calls)}", "expires_in": 3600}

    monkeypatch.setattr(vertex_auth_module, "request_access_token", _fake_request_access_token)

    provider = vertex_auth_module.VertexAccessTokenProvider(
        service_account_info=info,
        logger=MagicMock(),
    )

    first = await provider.get_token()
    second = await provider.get_token()
    assert first == second == "token1"
    assert len(calls) == 1

    provider._token_cache = vertex_auth_module.CachedAccessToken(
        access_token="expired",
        expires_at=time.time() - 1,
    )
    third = await provider.get_token()
    assert third == "token2"
    assert len(calls) == 2
