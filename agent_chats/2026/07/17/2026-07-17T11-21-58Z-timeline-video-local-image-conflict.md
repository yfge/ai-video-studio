## User Prompt

Clicking Timeline clip video generation returned HTTP 409. After refreshing, Volcengine rejected `content[3].image_url` because the request passed a Docker-local image URL that the external Provider could not download. The user clarified that local images were not handled.

## Goals

- Replace the generic 409 with a safe stale-Timeline recovery path that preserves the human-review gate.
- Make Volcengine video generation accept local `/uploads` images without exposing Docker-only URLs.
- Keep explicit reference bindings auditable: never silently remove an invalid selected image.
- Validate the real Timeline 76 input without starting another billable Provider task.

## Changes

- Added HTTP status and FastAPI `detail` propagation to the shared frontend API response.
- On Timeline video-submit 409, fetch and apply the latest Timeline, clear the operator-review checkbox, and require a fresh review/click. No automatic paid retry is made.
- Added a shared Volcengine image-input adapter used by both async submit and synchronous generation paths.
- Resolve local `localhost`, loopback, configured internal backend, and `ai-video-backend` `/uploads` URLs against the configured upload directory; prevent path traversal.
- Read and verify local images with Pillow, derive the MIME from image bytes, and inline them as Base64 data URLs. The incident file has a `.png` suffix but JPEG bytes, so it becomes `data:image/jpeg;base64,...`.
- Enforce the Provider limits before submission: each inline image is below 30 MiB and total raw inline image bytes are below 45 MiB, leaving Base64/JSON headroom under the request limit.
- Fail before Provider submission when an explicit local/data reference is missing, invalid, or oversized instead of silently dropping a character/environment binding.
- Added backend coverage for local first/last frames, both reference field aliases, internal hosts, MIME sniffing, invalid/missing inputs, size limits, unsupported model behavior, and preserved public/data/asset references.
- Added frontend coverage for FastAPI conflict details, refresh-without-retry behavior, cleared human review, warning messaging, and non-conflict submission.

## Validation

- `cd ai-pic-backend && pytest -q tests/test_timeline_clip_video_rework_api.py tests/unit/services/video/test_timeline_clip_video_rework_submission.py tests/unit/services/video/test_video_task_duration_fallback.py tests/unit/test_volcengine_provider_video.py tests/unit/test_volcengine_provider_video_local_images.py` -> 29 passed.
- Backend Ruff check and format check for the three changed backend files -> passed.
- `cd ai-pic-frontend && npx tsx --test tests/timelineClipVideoReworkConflict.test.ts tests/timelineClipReworkControls.test.ts` -> 33 passed.
- `cd ai-pic-frontend && npm run lint` -> passed with 0 errors and 3 existing warnings.
- `cd ai-pic-frontend && npm run test` -> 437 passed and 9 failed; all 9 are the unchanged dirty Canvas WIP baseline (`ProductionCanvasChatBar` 5 and `ProductionCanvasPlanner` 4). Timeline tests passed.
- Host `python run_tests.py quick` could not start tests because Python 3.13 dependency resolution conflicts between pinned `pydantic==2.5.0` and `langchain-core==0.2.43` requiring `pydantic>=2.7.4` on that interpreter.
- Container `python run_tests.py quick` reached collection and stopped on 15 existing `ModuleNotFoundError: scripts.harness` errors because the backend-only container does not mount the repository-level harness package.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- Real, non-billable worker probe for `http://ai-video-backend:8000/uploads/1321c06378624d909b07f8e4c3d5ef7a.png` -> `data:image/jpeg;base64,`, length `1600455`; no HTTP Provider call was made.
- Celery inspect before restart -> no active tasks. Restarted `ai-video-celery-worker` and `ai-video-backend`; worker became ready and backend `/health` returned 200.
- Browser entry URL rendered Timeline 76 with the video model selector, human-review control, and generation button; Console had no errors.
- Browser/runtime evidence: `artifacts/runs/timeline-local-image-fix-20260717T110703Z/`.
- `pre-commit run --files <this scoped change>` -> passed after Prettier normalized five frontend files; the hook's backend quick gate and frontend lint both passed.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/arm64 ./docker/build_prod_images.sh` was attempted in non-pushing mode. The legacy builder produced no progress while scanning the 5.9 GiB dirty worktree context and was stopped after roughly two minutes; no image was completed or pushed. The default push-enabled invocation was not used because it would tag uncommitted content with the previous commit `5729c64b` and publish it.
- `git diff --check` -> passed.

## Next Steps

- The operator can re-open/review the selected clip and submit generation. A real Provider request was intentionally not made during validation to avoid generation cost.
- Repository-wide backend quick/full and frontend full gates still contain the unrelated baseline failures documented above.

## Linked Commits

- This commit.
