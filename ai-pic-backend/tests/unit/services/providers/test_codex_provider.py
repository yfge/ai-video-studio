import json
import stat
from pathlib import Path

import pytest

from app.services.providers.base import ProviderConfig
from app.services.providers.codex_payload import build_codex_payload, parse_codex_sse
from app.services.providers.codex_provider import CodexProvider, _CodexUnauthorized


def _write_auth(path: Path, token: str = "sk-test-token") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "auth_mode": "chatgpt",
                "tokens": {
                    "access_token": token,
                    "account_id": "acct-test",
                    "refresh_token": "refresh-test",
                },
            }
        ),
        encoding="utf-8",
    )
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return path


def test_codex_payload_uses_responses_shape():
    payload = build_codex_payload(
        messages=[
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ],
        model="gpt-5.4",
        max_tokens=128,
        temperature=0.2,
    )

    assert payload["model"] == "gpt-5.4"
    assert payload["instructions"] == "You are helpful."
    assert payload["stream"] is True
    assert payload["store"] is False
    assert payload["max_output_tokens"] == 128
    assert payload["temperature"] == 0.2
    assert payload["input"][0]["content"][0] == {
        "type": "input_text",
        "text": "Hi",
    }
    assert payload["input"][1]["content"][0] == {
        "type": "output_text",
        "text": "Hello",
    }


def test_codex_sse_parser_collects_text_and_usage():
    raw = (
        "event: response.output_text.delta\n"
        'data: {"type":"response.output_text.delta","delta":"Hello"}\n\n'
        "event: response.output_text.delta\n"
        'data: {"type":"response.output_text.delta","delta":" world"}\n\n'
        "event: response.completed\n"
        "data: "
        '{"type":"response.completed","response":{"usage":{"input_tokens":1}}}\n\n'
    )

    text, usage = parse_codex_sse(raw)

    assert text == "Hello world"
    assert usage == {"input_tokens": 1}


def test_codex_headers_use_cli_auth(tmp_path: Path):
    auth_path = _write_auth(tmp_path / "auth.json")
    provider = CodexProvider(
        ProviderConfig(name="codex", api_key=str(auth_path), base_url=None)
    )

    provider._reload_auth()
    headers = provider._headers()

    assert headers["Authorization"] == "Bearer sk-test-token"
    assert headers["chatgpt-account-id"] == "acct-test"
    assert headers["originator"] == "codex_cli_rs"
    assert headers["Accept"] == "text/event-stream"


@pytest.mark.asyncio
async def test_codex_generate_text_reloads_rotated_token_after_401(
    tmp_path: Path, monkeypatch
):
    auth_path = _write_auth(tmp_path / "auth.json", token="sk-old")
    provider = CodexProvider(
        ProviderConfig(name="codex", api_key=str(auth_path), base_url=None)
    )
    calls = {"count": 0}

    async def fake_get_client():
        provider._reload_auth()
        return object()

    async def fake_post(_client, payload):
        calls["count"] += 1
        assert payload["model"] == "gpt-5.4"
        if calls["count"] == 1:
            _write_auth(auth_path, token="sk-new")
            raise _CodexUnauthorized("401")
        return "recovered", {"output_tokens": 1}

    monkeypatch.setattr(provider, "get_client", fake_get_client)
    monkeypatch.setattr(provider, "_post", fake_post)

    result = await provider.generate_text("hello", model="gpt-5.4")

    assert result.success is True
    assert result.data == "recovered"
    assert result.usage == {"output_tokens": 1}
    assert provider._token == "sk-new"
    assert calls["count"] == 2
