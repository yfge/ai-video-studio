#!/usr/bin/env python3
"""Run a browser validation scenario and persist evidence artifacts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import ensure_run_dir, update_summary, write_json
from scripts.harness.scenarios import BROWSER_SCENARIOS


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
    parser.add_argument("--episode-id", default=os.getenv("HARNESS_EPISODE_ID", "124"))
    return parser.parse_args()


def scenario_url(args: argparse.Namespace) -> str:
    scenario = BROWSER_SCENARIOS[args.scenario]
    path = scenario.path.format(
        virtual_ip_id=args.virtual_ip_id,
        episode_id=args.episode_id,
    )
    return f"{args.base_url.rstrip('/')}{path}"


def run_playwright(
    url: str, screenshot_path: Path, args: argparse.Namespace
) -> dict[str, object]:
    js = r"""
const fs = require("fs");
const { chromium } = require("@playwright/test");

(async () => {
  const [url, requiredText, screenshotPath, username, password, baseUrl, requiresAuth] = process.argv.slice(1);
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const consoleMessages = [];
  const requests = [];
  page.on("console", msg => consoleMessages.push({ type: msg.type(), text: msg.text() }));
  page.on("requestfinished", req => requests.push({ method: req.method(), url: req.url() }));
  if (requiresAuth === "true" && username && password) {
    await page.goto(baseUrl + "/login", { waitUntil: "networkidle" });
    await page.fill('input[name="username"]', username);
    await page.fill('input[name="password"]', password);
    await Promise.all([
      page.waitForLoadState("networkidle"),
      page.click('button[type="submit"]'),
    ]);
  }
  await page.goto(url, { waitUntil: "networkidle" });
  const content = await page.content();
  const title = await page.title();
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const result = {
    engine: "playwright",
    ok: content.includes(requiredText),
    currentUrl: page.url(),
    title,
    console: consoleMessages.slice(-20),
    network: requests.slice(-20),
  };
  await browser.close();
  fs.writeFileSync(1, JSON.stringify(result));
})().catch(err => {
  fs.writeFileSync(2, String(err && err.stack ? err.stack : err));
  process.exit(1);
});
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(js)
        script_path = Path(handle.name)
    command = [
        "node",
        str(script_path),
        url,
        BROWSER_SCENARIOS[args.scenario].required_text,
        str(screenshot_path),
        args.username,
        args.password,
        args.base_url.rstrip("/"),
        "true" if BROWSER_SCENARIOS[args.scenario].requires_auth else "false",
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    script_path.unlink(missing_ok=True)
    if completed.returncode != 0:
        return {"engine": "playwright", "ok": False, "error": completed.stderr.strip()}
    return json.loads(completed.stdout or "{}")


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

    attempts = [
        {
            "engine": "chrome_devtools_mcp",
            "ok": False,
            "reason": "CLI harness cannot attach to the in-session MCP transport.",
        }
    ]

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
    evidence = {
        "scenario": args.scenario,
        "url": url,
        "notes": scenario.notes,
        "attempts": attempts,
        "selected_engine": selected.get("engine"),
        "path_evidence": {
            "start": scenario.path,
            "final_url": selected.get("currentUrl"),
        },
        "console_evidence": selected.get("console", []),
        "network_evidence": selected.get("network", []),
        "result_evidence": {
            "title": selected.get("title"),
            "ok": selected.get("ok", False),
        },
        "screenshot": str(screenshot.relative_to(run_dir)),
    }
    write_json(run_dir / "browser_flow.json", evidence)
    write_json(run_dir / "console.json", evidence["console_evidence"])
    write_json(run_dir / "network.json", evidence["network_evidence"])
    update_summary(
        run_dir,
        browser_scenario=args.scenario,
        browser_status="passed" if selected.get("ok") else "failed",
        browser_engine=selected.get("engine"),
    )
    if selected.get("ok"):
        print(json.dumps({"ok": True, "engine": selected.get("engine")}))
        return 0
    print(json.dumps({"ok": False, "attempts": attempts}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
