import sys
import subprocess
from pathlib import Path
from types import SimpleNamespace

from scripts.harness import _common, browser_flow, run_golden_path


def test_browser_flow_writes_evidence_standard_metadata(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_common, "ARTIFACTS_ROOT", tmp_path / "runs")
    monkeypatch.setattr(
        browser_flow,
        "run_chrome_devtools",
        lambda url, screenshot_path, args: {
            "engine": "chrome_devtools_mcp",
            "ok": True,
            "currentUrl": url,
            "title": "Login",
            "console": [],
            "network": [],
            "domSnapshot": {"ok": True},
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "browser_flow.py",
            "--scenario",
            "login_smoke",
            "--run-id",
            "browser-standard-run",
            "--base-url",
            "http://localhost:8089",
        ],
    )

    assert browser_flow.main() == 0

    run_dir = tmp_path / "runs" / "browser-standard-run"
    browser_artifact = _common.read_json(run_dir / "browser_flow.json")
    summary = _common.read_json(run_dir / "summary.json")
    assert browser_artifact["standard_ids"] == ["STD-EVIDENCE-001"]
    assert summary["standard_ids"] == ["STD-EVIDENCE-001"]


def test_browser_driver_timeout_is_recorded_as_failed_attempt(
    tmp_path, monkeypatch
) -> None:
    def raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["node", "browser_driver.js"], timeout=7)

    monkeypatch.setattr(browser_flow.subprocess, "run", raise_timeout)

    result = browser_flow.run_browser_driver(
        "playwright",
        "http://localhost:8089/canvas",
        tmp_path / "canvas.png",
        SimpleNamespace(
            base_url="http://localhost:8089",
            browser_driver_timeout_seconds=7,
            chrome_debug_port=9333,
            chrome_debug_url="http://127.0.0.1:9333",
            password="",
            scenario="canvas_smoke",
            username="",
        ),
    )

    assert result == {
        "engine": "playwright",
        "ok": False,
        "error": "Browser driver timed out after 7s",
        "timeoutSeconds": 7,
    }


def test_golden_path_missing_input_carries_evidence_standard() -> None:
    result = run_golden_path.run_scenario(
        SimpleNamespace(
            scenario="episode_timeline_generation",
            run_id="golden-standard-run",
            api_url="http://localhost:8000",
            base_url="http://localhost:8089",
            username="geyunfei",
            password="redacted",
            script_id="",
            virtual_ip_id="",
            timeout_seconds=1,
        )
    )

    assert result["ok"] is False
    assert result["standard_ids"] == ["STD-EVIDENCE-001"]
    assert result["standard_refs"][0]["standard_doc"] == (
        "docs/standards/STD-EVIDENCE-001.md"
    )
