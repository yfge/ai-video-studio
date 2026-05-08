#!/usr/bin/env python3
"""Run a browser validation scenario and persist evidence artifacts."""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from shutil import copyfile

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import ensure_run_dir, update_summary, write_json
from scripts.harness.scenarios import BROWSER_SCENARIOS

PLACEHOLDER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl7l6kAAAAASUVORK5CYII="
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=sorted(BROWSER_SCENARIOS))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--base-url", default="http://localhost:8089")
    parser.add_argument("--username", default=os.getenv("HARNESS_USER", ""))
    parser.add_argument("--password", default=os.getenv("HARNESS_PASSWORD", ""))
    parser.add_argument(
        "--virtual-ip-id", default=os.getenv("HARNESS_VIRTUAL_IP_ID", "1")
    )
    parser.add_argument(
        "--environment-id", default=os.getenv("HARNESS_ENVIRONMENT_ID", "1")
    )
    parser.add_argument("--episode-id", default=os.getenv("HARNESS_EPISODE_ID", "124"))
    parser.add_argument("--script-id", default=os.getenv("HARNESS_SCRIPT_ID", "1"))
    parser.add_argument(
        "--chrome-debug-url",
        default=os.getenv("HARNESS_CHROME_DEBUG_URL", "http://127.0.0.1:9222"),
    )
    parser.add_argument(
        "--chrome-debug-port",
        type=int,
        default=int(os.getenv("HARNESS_CHROME_DEBUG_PORT", "9222")),
    )
    return parser.parse_args()


def scenario_url(args: argparse.Namespace) -> str:
    scenario = BROWSER_SCENARIOS[args.scenario]
    path = scenario.path.format(
        virtual_ip_id=args.virtual_ip_id,
        environment_id=args.environment_id,
        episode_id=args.episode_id,
        script_id=args.script_id,
    )
    return f"{args.base_url.rstrip('/')}{path}"


def browser_driver_config(
    url: str, screenshot_path: Path, args: argparse.Namespace
) -> dict[str, object]:
    scenario = BROWSER_SCENARIOS[args.scenario]
    return {
        "url": url,
        "requiredText": scenario.required_text,
        "screenshotPath": str(screenshot_path),
        "username": args.username,
        "password": args.password,
        "baseUrl": args.base_url.rstrip("/"),
        "requiresAuth": scenario.requires_auth,
        "debugUrl": args.chrome_debug_url.rstrip("/"),
        "debugPort": args.chrome_debug_port,
    }


def run_browser_driver(
    engine: str, url: str, screenshot_path: Path, args: argparse.Namespace
) -> dict[str, object]:
    script_path = Path(__file__).with_name("browser_driver.js")
    command = [
        "node",
        str(script_path),
        json.dumps(browser_driver_config(url, screenshot_path, args), ensure_ascii=False),
        engine,
    ]
    completed = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[2] / "ai-pic-frontend",
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return {"engine": engine, "ok": False, "error": completed.stderr.strip()}
    return json.loads(completed.stdout or "{}")


def run_playwright(url: str, screenshot_path: Path, args: argparse.Namespace) -> dict[str, object]:
    return run_browser_driver("playwright", url, screenshot_path, args)


def run_chrome_devtools(
    url: str, screenshot_path: Path, args: argparse.Namespace
) -> dict[str, object]:
    return run_browser_driver("chrome_devtools_mcp", url, screenshot_path, args)


def run_selenium(
    url: str, screenshot_path: Path, args: argparse.Namespace
) -> dict[str, object]:
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        if (
            BROWSER_SCENARIOS[args.scenario].requires_auth
            and args.username
            and args.password
        ):
            driver.get(f"{args.base_url.rstrip('/')}/login")
            driver.find_element(By.NAME, "username").send_keys(args.username)
            driver.find_element(By.NAME, "password").send_keys(args.password)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        driver.get(url)
        driver.save_screenshot(str(screenshot_path))
        source = driver.page_source
        return {
            "engine": "selenium",
            "ok": BROWSER_SCENARIOS[args.scenario].required_text in source,
            "currentUrl": driver.current_url,
            "title": driver.title,
            "console": [],
            "network": [],
        }
    finally:
        driver.quit()


def main() -> int:
    args = parse_args()
    scenario = BROWSER_SCENARIOS[args.scenario]
    run_dir = ensure_run_dir(args.run_id)
    url = scenario_url(args)
    screenshot = run_dir / "screenshots" / f"{args.scenario}.png"
    root_screenshot = run_dir / "screenshot.png"
    dom_snapshot_path = run_dir / "dom_snapshot.json"

    attempts = []

    result = run_chrome_devtools(url, screenshot, args)
    attempts.append(result)
    if not result.get("ok"):
        result = run_playwright(url, screenshot, args)
        attempts.append(result)
    if not result.get("ok"):
        try:
            result = run_selenium(url, screenshot, args)
        except Exception as exc:  # pragma: no cover - depends on host browser
            result = {"engine": "selenium", "ok": False, "error": str(exc)}
        attempts.append(result)

    selected = next(
        (item for item in reversed(attempts) if item.get("ok")), attempts[-1]
    )
    if screenshot.exists():
        copyfile(screenshot, root_screenshot)
    else:
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        screenshot.write_bytes(PLACEHOLDER_PNG)
        root_screenshot.write_bytes(PLACEHOLDER_PNG)
    write_json(dom_snapshot_path, selected.get("domSnapshot", {}) or {})
    browser_status = (
        "passed"
        if selected.get("ok") and selected.get("engine") == "chrome_devtools_mcp"
        else "degraded"
        if selected.get("ok")
        else "failed"
    )
    evidence = {
        "contract_version": 2,
        "scenario": args.scenario,
        "url": url,
        "notes": scenario.notes,
        "attempts": attempts,
        "selected_engine": selected.get("engine"),
        "selected_status": browser_status,
        "path_evidence": {
            "start": scenario.path,
            "final_url": selected.get("currentUrl"),
        },
        "console_evidence": selected.get("console", []),
        "network_evidence": selected.get("network", []),
        "dom_snapshot_artifact": str(dom_snapshot_path.relative_to(run_dir)),
        "result_evidence": {
            "title": selected.get("title"),
            "ok": selected.get("ok", False),
        },
        "screenshot": str(root_screenshot.relative_to(run_dir)),
        "scenario_screenshot": str(screenshot.relative_to(run_dir)),
    }
    write_json(run_dir / "browser_flow.json", evidence)
    write_json(run_dir / f"browser_flow.{args.scenario}.json", evidence)
    write_json(run_dir / "console.json", evidence["console_evidence"])
    write_json(run_dir / f"console.{args.scenario}.json", evidence["console_evidence"])
    write_json(run_dir / "network.json", evidence["network_evidence"])
    write_json(run_dir / f"network.{args.scenario}.json", evidence["network_evidence"])
    update_summary(
        run_dir,
        browser_scenario=args.scenario,
        browser_status=browser_status,
        browser_engine=selected.get("engine"),
    )
    if selected.get("ok"):
        print(json.dumps({"ok": True, "engine": selected.get("engine")}))
        return 0
    print(json.dumps({"ok": False, "attempts": attempts}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
