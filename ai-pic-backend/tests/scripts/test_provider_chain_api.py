import json
import sys
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests
from tests.scripts.provider_chain_fixtures import provider_payload

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT))

from scripts.harness.provider_chain_api import (  # noqa: E402
    generate_script,
    record_response,
    request_json,
)
from scripts.harness.provider_chain_payloads import TEXT_MODEL  # noqa: E402


def test_record_response_includes_request_duration() -> None:
    response = requests.Response()
    response.status_code = 200
    response.url = "https://example.com/api"
    response.headers["x-request-id"] = "req-1"
    response.headers["x-harness-run-id"] = "run-1"
    response.elapsed = timedelta(seconds=1.234)
    response.request = requests.Request("POST", response.url).prepare()

    chain: list[dict[str, object]] = []
    record_response(chain, response, label="seedance-video-1")

    assert chain == [
        {
            "label": "seedance-video-1",
            "method": "POST",
            "url": "https://example.com/api",
            "status_code": 200,
            "request_id": "req-1",
            "harness_run_id": "run-1",
            "duration_seconds": 1.234,
        }
    ]


def test_request_json_raises_with_response_body() -> None:
    response = requests.Response()
    response.status_code = 400
    response.url = "https://example.com/api"
    response._content = b'{"detail":"AccountOverdueError"}'
    response.request = requests.Request("POST", response.url).prepare()

    class _Session:
        def request(self, method, url, timeout, **kwargs):
            return response

    chain: list[dict[str, object]] = []
    with pytest.raises(requests.HTTPError, match="AccountOverdueError"):
        request_json(
            _Session(),
            "POST",
            response.url,
            chain=chain,
            label="seedance-video-1",
            timeout=1,
        )

    assert chain[0]["response_body"] == '{"detail":"AccountOverdueError"}'


def test_request_json_records_transport_error_without_response() -> None:
    class _Session:
        def request(self, method, url, timeout, **kwargs):
            raise requests.ConnectionError(
                "('Connection aborted.', RemoteDisconnected())"
            )

    chain: list[dict[str, object]] = []
    with pytest.raises(requests.ConnectionError):
        request_json(
            _Session(),
            "POST",
            "https://example.com/api/v1/ai/generate/text",
            chain=chain,
            label="deepseek-script",
            timeout=1,
        )

    assert chain == [
        {
            "label": "deepseek-script",
            "method": "POST",
            "url": "https://example.com/api/v1/ai/generate/text",
            "error": "ConnectionError: ('Connection aborted.', RemoteDisconnected())",
        }
    ]


def test_generate_script_records_raw_content_on_parse_failure() -> None:
    raw_content = '{"title":"坏剧本","scenes":[{"plot":"未闭合}'
    response = requests.Response()
    response.status_code = 200
    response.url = "https://example.com/api/v1/ai/generate/text"
    response._content = (
        '{"success":true,"data":{"provider":"deepseek","model":"'
        + TEXT_MODEL
        + '","content":'
        + json.dumps(raw_content)
        + "}}"
    ).encode("utf-8")
    response.request = requests.Request("POST", response.url).prepare()
    response.elapsed = timedelta(seconds=0.5)

    class _Session:
        def request(self, method, url, timeout, **kwargs):
            return response

    payload = {"request_chain": [], "key_artifacts": {}}
    args = SimpleNamespace(
        api_url="https://example.com",
        mode="smoke",
        script_premise=None,
        timeout_seconds=1,
    )

    with pytest.raises(ValueError, match="script_json_parse_failed"):
        generate_script(_Session(), args, payload)

    assert payload["request_chain"][0]["label"] == "deepseek-script"
    assert payload["request_chain"][0]["status_code"] == 200
    error = payload["key_artifacts"]["script_generation_error"]
    assert error["provider"] == "deepseek"
    assert error["model"] == TEXT_MODEL
    assert error["raw_content"] == raw_content
    assert error["error"].startswith("JSONDecodeError:")


def test_generate_script_disables_deepseek_streaming_and_thinking() -> None:
    raw_content = provider_payload()["key_artifacts"]["script"]["raw_content"]
    response = requests.Response()
    response.status_code = 200
    response.url = "https://example.com/api/v1/ai/generate/text"
    response._content = (
        '{"success":true,"data":{"provider":"deepseek","model":"'
        + TEXT_MODEL
        + '","content":'
        + json.dumps(raw_content)
        + "}}"
    ).encode("utf-8")
    response.request = requests.Request("POST", response.url).prepare()
    response.elapsed = timedelta(seconds=0.5)

    class _Session:
        def __init__(self) -> None:
            self.json_body = None

        def request(self, method, url, timeout, **kwargs):
            self.json_body = kwargs.get("json")
            return response

    payload = {"request_chain": [], "key_artifacts": {}}
    args = SimpleNamespace(
        api_url="https://example.com",
        mode="full-30s",
        script_premise=None,
        timeout_seconds=1,
    )
    session = _Session()

    script = generate_script(session, args, payload)

    assert script["title"] == "奖金清零"
    assert session.json_body["stream"] is False
    assert session.json_body["thinking"] is False
