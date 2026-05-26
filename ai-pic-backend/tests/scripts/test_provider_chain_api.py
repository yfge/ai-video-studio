import sys
from datetime import timedelta
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT))

from scripts.harness.provider_chain_api import record_response  # noqa: E402


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
