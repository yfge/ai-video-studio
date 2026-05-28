import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT))

from scripts.harness.provider_chain_regression import _failure_category  # noqa: E402


def test_failure_category_classifies_image_generation_endpoint() -> None:
    assert (
        _failure_category(
            "500 Server Error for url: "
            "http://localhost:8000/api/v1/virtual-ips/62/images/generate"
        )
        == "image_persistence_failed"
    )


def test_failure_category_classifies_provider_billing_evidence() -> None:
    payload = {
        "request_chain": [
            {
                "label": "seedance-video-1",
                "status_code": 400,
                "response_body": '{"detail":"AccountOverdueError: overdue balance"}',
            }
        ]
    }

    assert (
        _failure_category("400 Client Error for url: /api/v1/ai/generate/video", payload)
        == "provider_billing_or_quota_failed"
    )


def test_failure_category_classifies_script_json_parse_error() -> None:
    assert (
        _failure_category(
            "JSONDecodeError: Unterminated string starting at: line 3 column 14"
        )
        == "script_generation_failed"
    )


def test_failure_category_classifies_api_transport_error() -> None:
    payload = {
        "request_chain": [
            {
                "label": "deepseek-script",
                "error": "ConnectionError: ('Connection aborted.', RemoteDisconnected())",
            }
        ]
    }

    assert _failure_category("ConnectionError: request failed", payload) == (
        "api_transport_failed"
    )
