## User Prompt

继续推进无限画布的功能，并确认当前还有哪些能力没有完成。

## Goals

- 让无限画布可以在聊天规划时填写关键生产上下文。
- 让已执行节点的产物回填到下游节点，解除可满足的 blocked 输入。
- 补齐 `brief.compose` 与 `asset.select` 的画布执行入口，避免后台执行链在早期节点断开。
- 补齐画布运行保存/恢复、动态连线、媒体参数控制和 run 级摘要。
- 为 `/canvas` 增加 harness smoke 场景，并尝试产出 AP/browser 证据。

## Changes

- Added reusable production canvas context parsing for virtual IP, environment, episode, script, and task IDs.
- Added context inputs to the canvas chat bar and included parsed IDs in skill-plan requests.
- Propagated node outputs across canvas state so downstream required inputs can be satisfied after upstream execution.
- Added immediate backend execution handlers for `brief.compose` and `asset.select`.
- Added server-backed canvas run restore and saved-state update APIs.
- Added canvas Run ID save/restore controls and conversion between UI state and API state.
- Added dynamic canvas edge state, SVG rendering, node-level edge edit controls, and edge persistence.
- Added debounced autosave after a canvas run exists, with latest-state coalescing during rapid edits.
- Enhanced `report.summarize` so a canvas `run_id` can produce node, edge, status, and dispatched-task evidence without requiring a separate `task_id`.
- Extended `report.summarize` media evidence with task lineage, provider/model counts, numeric usage totals, provider task IDs, cost, frame indexes, result paths, and error fields from completed media tasks.
- Added image/video candidate controls for frame indexes, model, reference-image requirement, aspect ratio, duration, FPS, resolution, ratio, and fixed camera.
- Wired those media controls through the frontend execute payload into existing storyboard image/video queue payloads.
- Added the `canvas_smoke` browser harness scenario for `/canvas`.
- Split production canvas executor tests, registry tests, interaction controls, and skill-node mapping helpers to keep files within repository size limits.

## Validation

- `git diff --check` (passes)
- `python scripts/check_repo_docs.py` (passes)
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only) $(git ls-files --others --exclude-standard)` (passes)
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvasBoard.test.tsx tests/productionCanvasPersistence.test.tsx tests/productionCanvasMediaControls.test.tsx` (9 passing)
- `cd ai-pic-backend && pytest tests/unit/test_production_canvas_skill_plan.py tests/unit/test_production_canvas_executor.py tests/unit/test_production_canvas_skill_registry.py tests/unit/test_production_canvas_run_persistence.py tests/integration/test_production_canvas_media_api.py -q` (13 passing)
- `cd ai-pic-frontend && npm run lint` (passes with 3 existing warnings)
- `cd ai-pic-frontend && npm run build`
- `PYTHONPATH=. pytest tests/harness/test_runtime_evidence_standards.py -q`
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` (backend and frontend production images built locally without pushing; image tag was current HEAD `db4528c7`)
- `pre-commit run --all-files` was attempted. It failed on existing repo-wide ruff/import issues and the backend quick gate import error `cannot import name 'coerce_timeline_shot_plan_payload' from 'app.services.timeline_shot_plan_payloads'`; the hook also auto-modified unrelated historical files, which were reverted to keep this commit scoped.
- Lite harness stack started manually after `scripts/harness/bootstrap_worktree.sh --mode lite` exited 137 before writing output; Docker compose then built and started project `harness-ai-video-studio--7327729`.
- `python scripts/harness/doctor.py --run-id canvas-infinite-trace-20260622T090528Z --frontend-url http://localhost:3229 --api-url http://localhost:8229 --nginx-url http://localhost:9229 --env-file docker/.env.harness.canvas-infinite-trace-20260622T090528Z` (`doctor: ok`).
- Seeded the isolated SQLite harness DB with the `geyunfei` operator account; `POST http://localhost:9229/api/v1/auth/login` returned an access token.
- `GET http://localhost:9229/canvas` returned 200 and the Next.js login-check shell.
- `python scripts/harness/browser_flow.py --scenario canvas_smoke --run-id canvas-infinite-trace-20260622T090528Z --base-url http://localhost:9229 --username geyunfei --password 'Gyf@845261' --chrome-debug-port 9323 --chrome-debug-url http://127.0.0.1:9323` failed because local Chrome DevTools did not expose `/json/version`, and headless Chromium was killed by the host with `SIGKILL`.
- Manual headed Chromium fallback also failed with `SIGKILL`; evidence recorded at `artifacts/runs/canvas-infinite-trace-20260622T090528Z/browser_flow.canvas_manual_chromium.json`.
- Direct Chrome CDP validation succeeded by launching `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` with an isolated user data directory and `--remote-debugging-port=9333`, opening `/login`, authenticating with a browser-context `/api/v1/auth/login` fetch, setting `auth_token` and `user_info`, then navigating to `http://localhost:9229/canvas`.
- CDP evidence: `artifacts/runs/canvas-infinite-trace-20260622T090528Z/browser_flow.canvas_cdp.json`; screenshot: `artifacts/runs/canvas-infinite-trace-20260622T090528Z/screenshots/canvas_cdp.png`.
- CDP DOM evidence showed the operator shell and `创作画布` page, Run ID save/restore controls, the visible production chain, node details, edge controls, and 7 rendered canvas edges with only 200-level captured network responses for the page flow.

## Next Steps

- Standardize the direct Chrome CDP fallback into `scripts/harness/browser_flow.py` if host `SIGKILL` continues to prevent Playwright/headless Chromium fallback on this machine.
- Add full media-provider E2E evidence once a completed image/video generation run is available in the harness data set.

## Linked Commits

- Pending.
