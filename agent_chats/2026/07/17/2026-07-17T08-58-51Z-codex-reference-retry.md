---
id: 2026-07-17T08-58-51Z-codex-reference-retry
date: "2026-07-17T08:58:51Z"
participants: [user, codex]
models: [gpt-5]
tags: [codex, storyboard, timeline, references, retry]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/tasks.py
  - ai-pic-backend/app/services/task_dispatch.py
  - ai-pic-backend/app/services/providers/codex_image.py
  - ai-pic-backend/app/services/providers/codex_image_payload.py
  - ai-pic-backend/app/services/providers/codex_image_references.py
  - ai-pic-backend/app/services/providers/codex_provider.py
  - ai-pic-backend/tests/test_task_start_dispatch.py
  - ai-pic-backend/tests/unit/test_codex_image.py
  - ai-pic-backend/tests/unit/test_codex_image_references.py
summary: Repair Codex reference-image delivery and retry Timeline clip storyboard task 6449 to completion.
---

## User Prompt

Fix Timeline clip storyboard task #6449, which failed because the Codex endpoint could not download a supplied reference-image URL before its timeout.

## Goals

- Identify which #6449 reference URL Codex could not fetch and why.
- Make configured media references reachable by Codex without changing stored business URLs.
- Retain the documented `file_id` upload path as a fallback for explicit URL-download failures.
- Ensure a failed Timeline clip storyboard task retries on the grid-storyboard worker, not the legacy storyboard worker.
- Retry #6449 and prove the generated asset is written back and visible.

## Changes

- Normalized configured custom OSS/CDN media URLs to the bucket's HTTPS OSS origin before building Codex image inputs. This fixes both the HTTP environment reference and the newer custom-domain character reference that the Codex fetcher rejected.
- Added Codex reference-file upload support using the ChatGPT Codex file-slot, Azure blob PUT, and uploaded-finalization protocol, and retry with `input_image.file_id` only after the endpoint reports an explicit reference URL download timeout.
- Split Codex image payload/SSE and reference preparation into focused provider modules to keep provider files within repository size limits.
- Moved persisted-task Celery routing out of the API controller into `task_dispatch.py` and routed `timeline_clip_storyboard` / `timeline_storyboard_grid` retries to `tasks.grid_storyboard_sheet_generate`.
- Added unit coverage for custom-domain-to-origin mapping, the Codex file upload protocol, URL-to-file-ID retry, normal URL success, and Timeline clip storyboard retry dispatch.

## Validation

- Reproduced #6449 with its two stored references. Both downloaded quickly from the backend container, but direct Codex probes returned `400 Unable to download content` for the custom-domain character URL and the HTTP environment URL. Both corresponding HTTPS OSS origin URLs returned `200` from the Codex endpoint.
- `pytest tests/test_task_start_dispatch.py tests/unit/test_codex_image.py tests/unit/test_codex_image_references.py -q --no-cov`: 14 passed.
- `ruff check`, `isort --profile=black --check-only`, `black --check`, and `git diff --check` passed for all touched Python files.
- `pre-commit run --files <exact staged paths>` passed, including the backend quick gate, repository docs/contracts, and ledger enforcement. Repository-wide `--all-files` was intentionally not used because the checkout contains unrelated concurrent WIP; the exact staged slice was validated instead.
- `python scripts/check_repo_contracts.py --mode diff <touched files>`: passed. `tasks.py` is now 231 lines and `task_dispatch.py` is 88 lines.
- `python scripts/check_repo_docs.py`: passed.
- A detached staged snapshot at `/private/tmp/ai-video-studio-task6449.ubTGUj` passed `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`; both backend and frontend production images built locally, and no image was pushed.
- `python run_tests.py quick --no-setup`: 2634 passed, 79 skipped, 1 unrelated existing failure in `tests/integration/test_single_video_project_api.py::test_single_video_canvas_plan_reuses_unique_prompt_asset` (`resolved_context.virtual_ip_id` was `None`). The failure reproduced alone and does not touch the Codex or task-dispatch paths. The setup-enabled command was also blocked by the repository's Python 3.13 dependency conflict (`pydantic==2.5.0` versus `langchain-core>=2.7.4`).
- Restarted `ai-video-backend` and `ai-video-celery-worker`. `POST /api/v1/tasks/6449/start` returned `200` and preserved task ID 6449. Worker logs showed `tasks.grid_storyboard_sheet_generate` and `POST https://chatgpt.com/backend-api/codex/responses HTTP/1.1 200 OK`.
- Task #6449 reached `completed` at `2026-07-17T08:46:25` with no error. Timeline 76 advanced from version 2 to 3 and attached media asset 578 at `https://resource.lets-gpt.com/ai-generated/clip-storyboard/image/20260717/084624/b4e6b05e.png`.
- Downloaded and visually inspected the 1774x887 output: it is a two-panel 2:1 storyboard with stable character, wardrobe, office environment, and distinct wide/medium compositions.
- Chrome DevTools transport at `127.0.0.1:9222` was unavailable (`HTTP Not Found`), so browser verification used the in-app Browser fallback. On `http://localhost:8090/tasks`, the exact #6449 card showed `已完成`; console errors and warnings were empty.

## Next Steps

- No blocking follow-up for #6449.
- The primary OSS-origin path is proven in the running worker. The `file_id` fallback is unit-tested and its slot/blob protocol was verified from the host, but the current Docker network cannot reliably reach the returned `*.oaiusercontent.com` blob host; keep the origin mapping healthy or repair that container route before relying on upload fallback alone.
- Track the unrelated single-video Canvas quick-suite failure separately.

## Linked Commits

- This commit.
