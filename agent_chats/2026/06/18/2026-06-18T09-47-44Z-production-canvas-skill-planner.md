## User Prompt

在现有基础上加一个无限画布的入口，是不是可以考虑？这种情况下是不是有一个聊天入口然后进行整体创建？

## Goals

- Add a chat-style entry on the production canvas for whole-chain creation.
- Model the entry as a skill-plan executor surface instead of a separate product workflow.
- Reuse existing IP and environment assets through backend repositories.
- Return dynamic canvas nodes from the backend and append them to the infinite canvas.

## Changes

- Added `POST /api/v1/production-canvas/plan` and registered it in the v1 API router.
- Added production canvas request/response schemas and a planner service that emits `production_canvas.v1` with `brief.compose`, `asset.select`, `script.generate`, `storyboard.plan`, `image.candidates`, `video.candidates`, `timeline.assemble`, and `report.summarize`.
- Added a backend skill registry with per-skill reuse targets for existing API, service, repository, worker, and artifact boundaries.
- Added a skill runner that returns `skill_results`; canvas nodes are now derived from backend skill execution results instead of hand-coded frontend logic.
- Added Task-backed persistence for each canvas skill-plan execution, returning `run_id` and `task_id` to the frontend for lineage.
- Marked downstream generation skills as blocked until an `episode_id` is bound; when an episode is present, those nodes become ready and carry the episode id in outputs.
- Added `POST /api/v1/production-canvas/execute` as the first real skill dispatcher. `script.generate` now queues the existing `SCRIPT_GENERATION` Celery task through a shared script generation queue service; missing `episode_id` returns a blocked skill result instead of dispatching.
- Extended canvas plan/execute context with `script_id`. Script-scoped skills now become ready when a script id is present and carry that id through the execution output.
- Added real dispatch for `storyboard.plan` through the existing `STORYBOARD_GENERATION` Celery worker and `timeline.assemble` through the existing `TIMELINE_PIPELINE` worker.
- Added real dispatch for `image.candidates` through the existing storyboard image queue and `STORYBOARD_IMAGE_GENERATION` worker.
- Added real dispatch for `video.candidates` through a shared storyboard video queue adapter that creates existing `VIDEO_GENERATION` tasks and calls the existing storyboard video worker.
- Added `report.summarize`, which reads an accessible existing `Task` record and returns task status, type, run lineage, result path, error state, and parameter-key evidence as a reviewable canvas node.
- Split production canvas execution helpers into `execution_common.py`, `executor.py`, and `media_execution.py` to stay inside service file-size contracts.
- Extracted shared script task queuing into `app.services.script.generation_queue` and updated the existing scripts generation endpoint to use it.
- Added shared queue services for canvas reuse: `app.services.storyboard.generation_queue.queue_storyboard_generation_task` and `app.services.script.timeline_pipeline_queue.queue_timeline_pipeline_task`.
- Added repository list methods for accessible Virtual IP and environment assets.
- Split asset selection into `services/production_canvas/asset_selection.py` and canvas node construction into `services/production_canvas/nodes.py`.
- Tightened asset selection so unmatched prompts do not silently fall back to unrelated IP assets; matched environments can still be selected independently.
- Added frontend API types/endpoints, `useProductionCanvasSkillPlanner`, and a `ProductionCanvasChatBar`.
- Added frontend rendering for backend reuse targets and execution outputs in the canvas inspector.
- Added frontend display of `canvas_run_id` and `canvas_task_id` in dynamically appended execution nodes.
- Added an inspector `后台执行` button for dynamic skill nodes; it calls the production canvas execute endpoint and updates the same node from the returned `skill_result`.
- Updated frontend execute requests to carry `script_id` from node outputs so script-scoped skills can dispatch from the canvas.
- Updated frontend execute requests to carry `task_id` from `task_id`, `dispatched_task_id`, or `canvas_task_id`, so Report nodes can summarize the current canvas run or any upstream dispatched task.
- Added frontend task evidence nodes after successful skill execution; the canvas now upserts the original skill node and appends a non-executable `Task #...` node showing returned task status, lineage, outputs, and reuse targets.
- Updated the canvas controller to append returned dynamic skill-result nodes while preserving existing canvas state.

## Validation

1. Local checks:

- TDD red checks before implementation:
  - `cd ai-pic-backend && pytest tests/unit/test_production_canvas_skill_plan.py::test_canvas_skill_plan_carries_script_context_for_downstream_execution -q` -> failed because `storyboard.plan` stayed `blocked` without script context support.
  - `cd ai-pic-backend && pytest tests/integration/test_production_canvas_api.py::test_production_canvas_execute_storyboard_skill_dispatches_existing_task tests/integration/test_production_canvas_api.py::test_production_canvas_execute_timeline_skill_dispatches_existing_task -q` -> failed because shared queue modules did not exist.
  - `cd ai-pic-frontend && npx tsx --test tests/productionCanvasBoard.test.tsx` -> failed on `script_id` missing from the execute request.
  - `cd ai-pic-backend && pytest tests/integration/test_production_canvas_api.py -q` -> failed for `image.candidates` and `report.summarize` because they still returned the generic blocked dispatcher; failed for `video.candidates` because `app.services.storyboard.video_generation_queue` did not exist.
  - `cd ai-pic-frontend && npx tsx --test tests/productionCanvasBoard.test.tsx` -> failed because Report execution did not send `task_id` from the canvas task output.
  - `cd ai-pic-frontend && npx tsx --test tests/productionCanvasBoard.test.tsx` -> failed after adding the `Task #77` assertion because execution updated the skill node but did not append a task evidence node.
- `cd ai-pic-backend && pytest tests/unit/test_production_canvas_skill_plan.py tests/integration/test_production_canvas_api.py tests/integration/test_production_canvas_media_api.py -q` -> pass, 14 tests.
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvasBoard.test.tsx` -> pass, 5 tests.
- `cd ai-pic-frontend && npx tsx --test $(find tests -type f \( -name '*.test.tsx' -o -name '*.test.ts' -o -name '*.test.js' \) ! -name 'toastProvider.test.tsx')` -> pass in an earlier run, 126 tests. A later repeated run was manually interrupted after hanging late in `EpisodeTimelineWorkspace`; no current-slice failure was observed before interruption.
- `cd ai-pic-frontend && npm run lint` -> pass with existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run build` -> initially failed on a `response.data` TypeScript narrowing issue in `useProductionCanvasSkillPlanner`; fixed by assigning `const plan = response.data`; rerun passed with `/canvas` included in the production route output.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <canvas skill planner files>` -> initially failed after adding media execution because `test_production_canvas_api.py` and `executor.py` exceeded file-size contracts; fixed by splitting media/report tests and execution handlers; rerun passed.
- `git diff --check` -> pass.
- `cd ai-pic-backend && python -m black ...` -> applied to production canvas service/test files; subsequent target tests and contracts passed.
- `cd ai-pic-backend && python -m black --check <production canvas, queue service, and tests>` -> pass.
- `cd ai-pic-frontend && npm run lint` -> pass with the same three existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run build` -> pass with `/canvas` in the route output.
- Port cleanup after browser validation: `lsof -nP -iTCP:8001 -sTCP:LISTEN || true` and `lsof -nP -iTCP:3101 -sTCP:LISTEN || true` -> no listeners.

2. Browser or MCP validation:

- Entry URL: `http://127.0.0.1:3100/canvas`.
- Chrome DevTools MCP: failed to connect to `http://127.0.0.1:9222/json/version` with `HTTP Not Found`; fell back to Playwright using system Google Chrome.
- User path: opened `/canvas`, followed auth redirect to `/login?next=%2Fcanvas`, logged in as `geyunfei`, filled `生产目标` with `基于林妹妹做第 4 集，办公室轻喜剧`, clicked `整体创建`.
- Network: real `POST http://localhost:8000/api/v1/auth/login` returned 200; real `POST http://localhost:8000/api/v1/production-canvas/plan` returned 200 with body containing 8 manifest skills and 8 skill results.
- Console: no material error or warning messages in the final browser run.
- Result: the canvas appended skill nodes, displayed `Asset Selection` with `IP 待确认；已选择环境：办公室`, and the inspector showed `后台复用` plus `Environment repository`.
- Screenshot: `artifacts/runs/production-canvas-skill-registry-1781776558569/canvas-skill-registry.png`.
- Follow-up fallback validation after run persistence:
  - Entry URL: `http://127.0.0.1:3101/canvas`, using temporary local backend `http://127.0.0.1:8001` because the existing `8000` listener returned 404 for the new route.
  - Chrome DevTools MCP still failed with `HTTP Not Found` on `127.0.0.1:9222/json/version`; used Playwright with system Google Chrome.
  - Network: `POST http://127.0.0.1:8001/api/v1/auth/login` -> 200; `POST http://127.0.0.1:8001/api/v1/production-canvas/plan` -> 200.
  - Response: `success=true`, `run_id=e1cd1e052c3f4b6b9d112d958ac08601`, `task_id=6071`, 8 skill results, 8 nodes.
  - Page evidence: selecting `Script Skill` showed `后台复用`, `required_inputs: episode_id`, `canvas_run_id`, and `canvas_task_id` in the inspector.
  - Screenshot: `artifacts/runs/production-canvas-skill-executor-1781786142604/canvas-skill-executor.png`.
- Follow-up fallback validation after execute button:
  - Entry URL: `http://127.0.0.1:3101/canvas`, temporary backend `http://127.0.0.1:8001`.
  - Chrome DevTools MCP still failed with `HTTP Not Found` on `127.0.0.1:9222/json/version`; used Playwright with system Google Chrome.
  - Network: login -> 200; `POST /api/v1/production-canvas/plan` -> 200; `POST /api/v1/production-canvas/execute` -> 200.
  - Plan response: `run_id=c3bedda562bf432db968513edae16d76`, `task_id=6072`, 8 skill results, 8 nodes.
  - Execute response: `skill=script.generate`, `status=blocked`, `required_inputs=["episode_id"]`.
  - Page evidence: inspector retained `canvas_run_id` and `canvas_task_id`, showed `后台执行`, and updated `Script Skill` to `Script Skill 等待剧集上下文`.
  - Screenshot: `artifacts/runs/production-canvas-execute-button-1781787116071/canvas-execute-button.png`.
- Follow-up fallback validation after script-context dispatch:
  - Entry URL: `http://127.0.0.1:3101/canvas`, temporary backend `http://127.0.0.1:8001`.
  - Chrome DevTools MCP still failed with `HTTP Not Found` on `127.0.0.1:9222/json/version`; used Playwright with system Google Chrome.
  - Validation setup: used a real accessible script id (`script_id=143`) and preloaded the canvas state with Storyboard and Timeline skill nodes carrying `script_id`.
  - Network: login -> 200; `POST /api/v1/production-canvas/execute` for `storyboard.plan` -> 200; `POST /api/v1/production-canvas/execute` for `timeline.assemble` -> 200.
  - Execute responses: `storyboard.plan` returned `task_id=6073`, `status=running`, `script_id=143`; `timeline.assemble` returned `task_id=6074`, `status=running`, `script_id=143`.
  - Console: no browser console errors collected in the final fallback run.
  - Page evidence: inspector showed `已提交现有时间线流水线任务`, `Timeline pipeline queue`, `script_id: 143`, `dispatched_task_id: 6074`, and `task_status: pending`.
  - Screenshot: `artifacts/runs/production-canvas-script-context-1781788108974/canvas-script-context-dispatch.png`.
- Follow-up fallback validation after image/video/report dispatch:
  - Entry URL: `http://127.0.0.1:3101/canvas`, temporary backend `http://127.0.0.1:8001`.
  - Chrome DevTools MCP still failed with `HTTP Not Found` on `127.0.0.1:9222/json/version`; used Playwright with system Google Chrome.
  - Validation setup: logged in as `geyunfei`, called real `POST /api/v1/production-canvas/plan` for `script_id=15`, then preloaded canvas nodes carrying `script_id=15`, `canvas_run_id=669a5326964c41a48320b5cbe1c095bd`, and `canvas_task_id=6075`.
  - Network: login -> 200; plan -> 200; execute `image.candidates` -> 200; execute `video.candidates` -> 200; execute `report.summarize` -> 200.
  - Execute responses: `image.candidates` returned `task_id=6076`, `status=running`, `queued_frame_count=4`; `video.candidates` returned `task_id=6077`, `status=running`, `frame_count=7`; `report.summarize` returned `task_id=6075`, `status=review`, `source_kind=production_canvas_run`.
  - Console: only React DevTools and HMR development messages, no material errors.
  - Screenshot: `artifacts/runs/production-canvas-media-1781789249984/canvas-media-report-execution.png`.
  - Network evidence: `artifacts/runs/production-canvas-media-1781789249984/network.json`.
- Follow-up fallback validation after task evidence nodes:
  - Entry URL: `http://127.0.0.1:3101/canvas`, temporary backend `http://127.0.0.1:8001`.
  - Chrome DevTools MCP still failed with `HTTP Not Found` on `127.0.0.1:9222/json/version`; used Playwright with system Google Chrome.
  - Validation setup: logged in as `geyunfei`, called real plan for `script_id=15`, preloaded canvas nodes, and clicked `后台执行` for Image, Video, and Report.
  - Network: execute `image.candidates` -> 200 with `task_id=6079`; execute `video.candidates` -> 200 with `task_id=6080`; execute `report.summarize` -> 200 with `task_id=6078`.
  - Page evidence: Playwright waited for visible labels matching `Task #... 已提交现有分镜图片候选任务`, `Task #... 已提交现有分镜视频候选任务`, and `Task #6078 已汇总现有任务证据`.
  - Console: only React DevTools and HMR development messages, no material errors.
  - Screenshot: `artifacts/runs/production-canvas-task-nodes-1781789811570/canvas-task-evidence-nodes.png`.
  - Network evidence: `artifacts/runs/production-canvas-task-nodes-1781789811570/network.json`.

3. Conflict signals and corrections:

- Initial real browser evidence showed the planner selected unrelated IP `斌哥` when `林妹妹` was not matched in the accessible asset window.
- The planner was corrected to only select Virtual IPs on explicit id or text/tag match, while allowing independent environment matches.
- A unit test now covers the unmatched fallback case.
- An optional refactor of `storyboard/generation.py` to use the new storyboard queue service caused `check_repo_contracts.py --mode diff` to flag historical route-size/direct-query violations in that unchanged hotspot. The optional endpoint refactor was removed; canvas still reuses the new queue service directly and contracts pass for the actual changed boundary.
- A live DB lookup using the broad script repository ordering hit MySQL `(1038, 'Out of sort memory')`; validation switched to a narrow `SELECT scripts.id ... ORDER BY id DESC LIMIT 5` to choose `script_id=143` without broad row sorting.
- `cd ai-pic-backend && python run_tests.py quick` did not reach tests because the local Python 3.13 resolver conflicts with pinned dependencies: `langchain-core==0.2.43` requires `pydantic>=2.7.4` while the repo pins `pydantic==2.5.0`.
- Browser validation initially sent a plan request before `auth_token` had been written because `waitForURL(/canvas/)` matched the login page query `next=/canvas`; the script was corrected to wait for `localStorage.auth_token` before calling the plan API.

## Next Steps

- Add explicit user confirmation before chaining selected assets into script/storyboard execution.
- Add a UI affordance for binding `episode_id`, `script_id`, and `task_id` from existing projects instead of preloading localStorage during validation.
- Decide whether unmatched named entities should trigger asset creation, search suggestions, or a blocking clarification node.

## Linked Commits

- Pending.
