## User Prompt

`/goal 视频部分没有看到绑定 IP 环境`

## Goals

- Make the selected Timeline video clip production panel show the IP/environment binding that will be used for video generation.
- Ensure video rework requests preserve selected role IPs, IP reference images, and environment reference images instead of limiting them to storyboard generation.
- Keep the fix Timeline-first and scoped to the selected clip video path.

## Changes

- Added a `片段视频绑定` summary inside the clip video rework card, showing selected role IPs plus IP/environment reference image counts.
- Extended the frontend video rework payload builder and API types to submit `character_virtual_ip_ids`, `character_reference_images`, and `environment_reference_images`.
- Extended the backend video rework schema to accept those fields.
- Added `timeline_clip_video_rework_context.py` so queueing a video rework task resolves selected bindings through the existing clip storyboard context logic, merges the resulting references into provider `reference_images`, and stores `bound_context` in task parameters.
- Moved clip prompt fallback into `timeline_clip_video_rework_helpers.py` to keep the queue service below repo file-size limits.
- Added frontend and backend regression tests for video rework IP/environment bindings.

## Validation

1. Local checks:

- `npm run lint` in `ai-pic-frontend` -> pass with 0 errors and 3 existing warnings.
- `npm run test` in `ai-pic-frontend` -> pass, 49/49 tests.
- `ai-pic-backend/.venv/bin/python -m pytest tests/test_timeline_clip_video_rework_context_api.py tests/test_timeline_clip_video_grid_rework_api.py::test_timeline_clip_video_rework_uses_clip_storyboard_panel_reference tests/test_timeline_clip_video_grid_rework_api.py::test_timeline_clip_video_rework_uses_storyboard_grid_panel_reference tests/unit/services/video/test_timeline_clip_video_rework_submission.py -v` -> pass, 5/5 tests.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> pass after extracting the bound-context helper and moving the new API test to its own file.
- `git diff --check` -> pass.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089`.
- Local stack probe: `curl -I --max-time 5 http://localhost:8089` -> 200 from Nginx/Next.js.
- Chrome DevTools attempt: failed twice because `http://127.0.0.1:9222/json/version` returned 404 from an existing Google Chrome process, so CDP was unavailable.
- Playwright fallback attempt: failed with bundled Chromium missing from `~/Library/Caches/ms-playwright`; retrying with system Chrome at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` launched then exited with `SIGKILL`.
- API fallback probe: authenticated against local `POST /api/v1/auth/login` and found existing episode `6`, timeline `66`, version `3`, video clip `video_scene_001_beat_001_001`.
- Result: real browser UI verification remains blocked by browser automation availability. Component tests and backend API tests cover the changed UI payload and queue contract.

3. Conflict signals and corrections:

- Initial assumption: the issue might be only missing UI copy in the video panel.
- Contradicting evidence: frontend tests showed video submit did not send selected IP/environment bindings, and backend RED test showed the video rework schema ignored those fields.
- Correction: submit and persist bindings through the video rework request path, not only through storyboard generation.
- Final verified state: automated frontend/backend tests prove selected IP/environment bindings appear in the video card payload and are merged into backend provider `reference_images`.

4. Commit-prep validation:

- The broader clip storyboard/keyframe follow-up re-ran the affected backend and frontend tests after Black/Prettier hook formatting.
- `cd ai-pic-backend && pytest tests/test_timeline_clip_keyframe_api.py tests/test_timeline_clip_keyframe_processor.py tests/test_timeline_clip_video_rework_context_api.py -q` -> pass, 4/4 tests.
- `cd ai-pic-frontend && npm run test` -> pass, 53/53 tests.
- `cd ai-pic-frontend && npm run lint` -> pass with the same 3 existing warnings.
- `cd ai-pic-frontend && npm run build` -> pass.
- `SKIP=backend-pytest pre-commit run --files <changed files>` -> pass for non-backend-quick hooks; `backend-pytest` was skipped because the repo's broader backend collection still has unrelated baseline import errors in production quality tests.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode audit` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <changed and untracked files>` -> pass.
- `git diff --check` -> pass.
- `./docker/build_prod_images.sh` -> pass and push backend/frontend production images with tag `a04c0fa5`.

## Next Steps

- Re-run Chrome/Playwright UI validation after fixing the local CDP/browser automation environment.

## Linked Commits

- None yet.
