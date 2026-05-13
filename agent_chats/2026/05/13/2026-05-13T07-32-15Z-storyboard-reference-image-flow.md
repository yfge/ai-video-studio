## User Prompt

全流程回归 ，生成分镜的时候要先生成对应的画面，同时画面要有参考 图

Follow-up: 直接使用直接provider 看实际效果，生图用gpt-img-2 ,视频用seedance 2.0

Follow-up: implement the story -> script -> storyboard completeness plan: share storyboard image task enqueueing across production script generation and one-click timeline pipeline, preflight reference images, record child-task metadata, isolate the legacy sync 500, and align `SceneBeat.characters_involved` with the backend contract.

## Goals

- When storyboard frames are generated from the timeline pipeline, queue storyboard image generation immediately after frame placeholder creation.
- Require storyboard image tasks in this flow to use frame/environment/character reference images, failing clearly when a target frame has none.
- In the frontend storyboard workspace, prevent video task creation until the target storyboard frame already has a generated image; if missing, queue reference-based image generation first.
- Run the closest full-flow regression without spending external image/video provider calls unnecessarily.
- Make the production async script path and one-click timeline path both end at storyboard placeholders plus explicit image-child-task metadata.
- Keep parent task semantics clear: parent completion means script/timeline/storyboard placeholders are complete; child storyboard image task creation is recorded separately and skips frames without references.
- Keep `/scripts/generate` as a debug/light sync route while preventing its quality gate mock from obscuring normalized-scene sync coverage.

## Changes

- Added `require_reference_images` to the storyboard image API request and Celery task payload.
- Added `queue_storyboard_image_generation(...)` so the one-click timeline pipeline now runs as audio -> Timeline Spec -> storyboard placeholders -> storyboard image task.
- Added repository helpers for storyboard media task/script lookups, aspect ratio resolution, and image-frame persistence to keep route and task code inside repository boundaries.
- Updated storyboard image task processing to raise a clear failure when reference images are required but the frame has none.
- Updated the storyboard workspace so scene/all/timeline-generated storyboard completion queues reference-based start/end image generation for frames missing visuals.
- Updated scene video and single-frame video flows to queue image generation first when the target frame lacks a start image instead of creating a video task immediately.
- Preserved storyboard image generation options (`generation_profile`, `size`, `strength`, `count`) through the backend request schema and task payload after the direct provider run showed `size/count` were being ignored.
- Added backend regression coverage for required references and for the timeline pipeline's follow-up image task.
- Stored Playwright fallback evidence under `artifacts/runs/20260513T073008Z-storyboard-reference-first/`.
- Reworked storyboard image autogen into a shared service result object with reference-image preflight, queued/skipped frame indexes, and parent task metadata recording.
- Wired the shared enqueue/preflight service into both production async `run_auto_timeline_placeholders(...)` and one-click timeline pipeline generation.
- Split production hook annotation and timeline storyboard queue helpers into focused service modules to keep changed files below repo contract size limits.
- Updated timeline parent task parameters with `storyboard_image_generation.child_task_id`, queued frame count, and skipped frame count.
- Updated `SceneBeat.characters_involved` frontend types to accept backend-compatible `dict | list | null`.
- Isolated the legacy `/scripts/generate` normalized-scene sync test by mocking the narrative quality gate, so it verifies scene sync rather than failing on deterministic mock content.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/test_storyboard_image_task_image_gen_persistence.py tests/unit/test_storyboard_image_task_reference_requirement.py tests/integration/test_timeline_pipeline_import_api.py -q` -> pass, 5 tests passed.
- `cd ai-pic-frontend && npm run lint` -> pass with existing warnings only; no errors.
- `cd ai-pic-frontend && npm run test` -> pass, 13 tests passed.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only)` -> pass.
- `git diff --check` -> pass.
- `python -m compileall ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_processor.py ai-pic-backend/app/api/v1/endpoints/storyboard/media.py ai-pic-backend/app/repositories/storyboard_media_repository.py ai-pic-backend/app/services/storyboard/storyboard_image_autogen.py ai-pic-backend/app/services/task_worker_storyboard_media.py` -> pass.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/episodes/137/workspace?tab=storyboard&scriptId=129`.
- User path: logged in via the local backend, opened the storyboard workspace for script `129`, clicked `为此场景批量生成视频`.
- Chrome DevTools: unavailable; `http://127.0.0.1:9222/json/version` returned HTTP Not Found, so the run used Playwright with the local Chrome channel.
- Network: Playwright intercepted external-task creation to avoid spending provider calls. The clicked video path sent one `POST /api/v1/scripts/129/storyboard/generate-images` and zero `POST /api/v1/scripts/129/storyboard/generate-video` calls.
- Decisive payload: `frames: [0,1,2,3,4]`, `keyframe_mode: "start_end"`, `start_enabled: true`, `end_enabled: true`, `require_reference_images: true`.
- Console: three Next dev HMR WebSocket 404 errors; no failed requests and no path-blocking console errors.
- Result: pass. The UI displayed the pre-image notice and did not create a video task before images existed.
- Evidence: `artifacts/runs/20260513T073008Z-storyboard-reference-first/playwright-storyboard-reference-first.json`, `storyboard-before-video-click.png`, `storyboard-after-video-click.png`.

3. Conflict signals and corrections:

- Initial browser attempt with Chrome DevTools failed due local CDP transport, not application behavior.
- The first Playwright attempt used CommonJS `require` under ESM and failed before opening the page.
- The second Playwright attempt used the default bundled Chromium, but the browser binary was not installed.
- The final run used the locally installed Chrome channel and completed the browser regression without external provider calls.

4. Direct provider validation:

- First direct run: script `129`, frame `0`, image model `openai:gpt-image-2`, video model `volcengine:seedance-2.0-i2v`.
- Image result: pass. Task `5982` completed with `start_image_url=https://resource.lets-gpt.com/ai-generated/storyboard/image/20260513/074411/b037ff31.png` and `end_image_url=https://resource.lets-gpt.com/ai-generated/storyboard/image/20260513/074533/d2756c99.png`; image metadata recorded `provider=openai`, `model_id=gpt-image-2`, `reference_images_count=1`.
- Video result: failed at provider submit. Parent task `5983` failed because Volcengine returned `InputImageSensitiveContentDetected.PrivacyInformation`, indicating the generated person image may contain real-person privacy information.
- Second direct run: script `130`, frame `0`, environment reference image only, image model `openai:gpt-image-2`, video model `volcengine:seedance-2.0-i2v`, prompt forced an empty old-house interior with no people.
- Image result: pass. Task `5984` completed with new generated images `start=https://resource.lets-gpt.com/ai-generated/storyboard/image/20260513/074838/87b798fd.png` and `end=https://resource.lets-gpt.com/ai-generated/storyboard/image/20260513/075013/a754c8eb.png`; metadata recorded `provider=openai`, `model_id=gpt-image-2`, `reference_images_count=1`.
- Video result: pass. Task `5985`, child video task `122`, provider task `cgt-20260513155018-6qm5q`, model resolved by Volcengine to `doubao-seedance-2-0-260128`, final video `https://resource.lets-gpt.com/ai-generated/videos/video/20260513/075531/411b097f.mp4`, last frame `https://resource.lets-gpt.com/ai-generated/video-last-frames/image/20260513/075532/69a20aff.png`.
- Direct provider evidence: `artifacts/runs/20260513T074239Z-direct-provider-gptimg2-seedance20/direct-provider-evidence.json` and `artifacts/runs/20260513T074706Z-direct-provider-env-gptimg2-seedance20/direct-provider-env-evidence.json`.
- Conflict signal: the direct image run requested `size=1536x1024`, but persisted image metadata showed `size=1024x1024`; this exposed that the storyboard image API schema did not preserve `size/count` options. The schema and regression test were updated after the run; no extra provider rerun was done to avoid additional external cost.

5. Post-provider fix validation:

- `cd ai-pic-backend && pytest tests/unit/test_storyboard_image_task_reference_requirement.py tests/integration/test_timeline_pipeline_import_api.py -q` -> pass, 4 tests passed.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only)` -> pass.
- `git diff --check` -> pass.
- `python -m compileall ai-pic-backend/app/api/v1/endpoints/storyboard/media.py` -> pass.

6. Story/script/storyboard chain implementation validation:

- `cd ai-pic-backend && pytest tests/integration/test_timeline_pipeline_import_api.py tests/unit/test_storyboard_image_task_reference_requirement.py tests/unit/services/audio/test_storyboard_from_timeline_spec.py tests/unit/services/script/test_production_storyboard_timeline_import.py tests/scripts/test_script_story_structure_sync.py -q` -> pass, 10 tests passed.
- `cd ai-pic-frontend && npm run lint` -> pass with existing warnings only; no errors.
- `cd ai-pic-frontend && npm run test` -> pass, 13 tests passed.
- `python scripts/check_repo_contracts.py --mode diff ...` with all changed backend/frontend files -> pass.
- `git diff --check` -> pass.
- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py ai-pic-backend/app/repositories/storyboard_media_repository.py ai-pic-backend/app/services/script/production_storyboard.py ai-pic-backend/app/services/script/production_storyboard_hooks.py ai-pic-backend/app/services/script/timeline_storyboard_queue.py ai-pic-backend/app/services/storyboard/storyboard_image_autogen.py` -> pass.

7. Browser validation after implementation:

- Command: `python scripts/harness/browser_flow.py --scenario episode_workspace_storyboard_smoke --run-id 20260513T101305Z-story-script-storyboard-chain --base-url http://localhost:8089 --username geyunfei --password 'Gyf@845261' --episode-id 137 --script-id 129`.
- Result: pass via Playwright fallback. Chrome DevTools timed out at `http://127.0.0.1:9222`, so status is recorded as degraded rather than Chrome-verified.
- Evidence: `artifacts/runs/20260513T101305Z-story-script-storyboard-chain/browser_flow.episode_workspace_storyboard_smoke.json`, `summary.json`, and `screenshots/episode_workspace_storyboard_smoke.png`.
- Console: local Next HMR WebSocket 404s only; no path-blocking request failure in the captured storyboard workspace.

8. Commit-time checks:

- `git diff --cached --check` -> pass.
- `pre-commit run --all-files` -> failed on existing all-repo issues outside this scoped change. The run also auto-touched many historical files via EOF/ruff hooks; those non-scope worktree edits were restored before commit.
- Blocking pre-commit failures included historical all-file ruff findings, existing `repo-contracts` oversized report for `ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_processor.py`, and backend quick gate import failure `cannot import name 'check_cliffhanger' from app.services.script_quality.checks`.
- `./docker/build_prod_images.sh` was not run for this scoped commit; prior targeted backend/frontend/browser validation above is the commit evidence.

## Next Steps

- No follow-up is required for the scoped implementation. Story-level one-click generation for all episodes remains intentionally out of scope until product asks for that new entrypoint.
- The person-frame Seedance rejection from direct-provider validation is provider safety behavior; use environment/no-person or approved non-sensitive character inputs for future Seedance smoke runs.

## Linked Commits

- Pending.
