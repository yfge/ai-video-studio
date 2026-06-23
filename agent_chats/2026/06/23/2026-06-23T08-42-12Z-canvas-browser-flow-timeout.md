---
id: 2026-06-23T08-42-12Z-canvas-browser-flow-timeout
date: 2026-06-23T08:42:12Z
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - production-canvas
  - harness
  - browser-evidence
related_paths:
  - scripts/harness/browser_flow.py
  - tests/harness/test_runtime_evidence_standards.py
  - agent_chats/2026/06/22/2026-06-22T08-26-53Z-canvas-context-unlock.md
summary: Added a browser-driver timeout guard so canvas browser validation cannot hang indefinitely, then revalidated the infinite canvas smoke scenario.
---

## User Prompt

/goal 整体完成无限画布功能

## Goals

- Confirm the current production canvas state from the repository instead of relying on memory.
- Close the remaining browser-validation reliability gap from the previous canvas ledger.
- Preserve canvas smoke evidence under `artifacts/runs/`.
- Keep delivery records linked to the actual canvas commit.

## Changes

- Added `--browser-driver-timeout-seconds` to `scripts/harness/browser_flow.py`, defaulting from `HARNESS_BROWSER_DRIVER_TIMEOUT_SECONDS` or `90`.
- Wrapped each Node browser-driver attempt with `subprocess.run(..., timeout=...)`.
- Converted browser-driver timeouts into structured failed attempts with `engine`, `ok: false`, `error`, and `timeoutSeconds`, so the harness can continue to later fallbacks and write diagnosable evidence.
- Added a regression test for timeout handling in `tests/harness/test_runtime_evidence_standards.py`.
- Backfilled the previous infinite-canvas ledger entry with the real commit `0a671ac4`.

## Validation

- `PYTHONPATH=. pytest tests/harness/test_runtime_evidence_standards.py::test_browser_driver_timeout_is_recorded_as_failed_attempt -q` -> failed before the implementation because `subprocess.TimeoutExpired` escaped from `run_browser_driver`.
- `PYTHONPATH=. pytest tests/harness/test_runtime_evidence_standards.py::test_browser_driver_timeout_is_recorded_as_failed_attempt -q` -> passed after the timeout guard was added.
- `python scripts/harness/browser_flow.py --scenario canvas_smoke --run-id canvas-timeout-check-20260623T000000Z --base-url http://localhost:9229 --username <redacted> --password <redacted> --chrome-debug-port 9334 --chrome-debug-url http://127.0.0.1:9334 --browser-driver-timeout-seconds 15` -> passed in 7.4s with `{"ok": true, "engine": "chrome_devtools_mcp"}`.
- Browser artifact: `artifacts/runs/canvas-timeout-check-20260623T000000Z/browser_flow.json` recorded `selected_engine=chrome_devtools_mcp`, `selected_status=passed`, `url=http://localhost:9229/canvas`, `result_evidence.ok=true`, and screenshot `screenshot.png`.
- DOM evidence: `artifacts/runs/canvas-timeout-check-20260623T000000Z/dom_snapshot.json` showed the authenticated `创作画布` page, Run ID save/restore controls, the visible production chain, node action buttons, and canvas controls.
- Existing issue confirmed before the fix: a prior `canvas_smoke` run had to be interrupted after more than 90 seconds while blocked inside the Playwright browser-driver subprocess.
- `pre-commit run --all-files` was not rerun for this harness-only patch because the previous canvas validation already documented existing repo-wide hook failures and unrelated auto-modification risk.
- `./docker/build_prod_images.sh` was not rerun for this harness-only patch because the change only affects local validation scripts/tests and no app runtime image content.

## Next Steps

- If future media-provider E2E data is available, add a full image/video execution browser path on top of the existing `canvas_smoke`.

## Linked Commits

- Pending.
