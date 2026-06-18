## User Prompt

- "而且失败了"
- Context: `video_scene_91_beat_4003_013` timeline clip storyboard generation failed after the user selected the Codex image model.

## Goals

- Verify the real failed task before changing code.
- Keep the user-selected model behavior, but avoid failing the whole storyboard sheet when Codex returns a transient overload error.
- Preserve existing request payload shapes and reference image flow.

## Changes

- Confirmed task `6070` (`Timeline clip storyboard - video_scene_91_beat_4003_013`) failed with `codex 错误: Our servers are currently overloaded. Please try again later.` using model `codex:gpt-image-2`.
- Confirmed task `6070` did include reference images: two character reference URLs and one environment reference URL, plus the combined `reference_images` list.
- Extracted storyboard image request normalization/call helpers into `ai-pic-backend/app/services/storyboard/storyboard_image_generation_request.py`.
- Added a Codex-overload-only fallback in `generate_storyboard_image_urls`: initial calls still use the selected `codex:*` model, then retry once with `volcengine:doubao-seedream-4-5-251128` when the error contains `overloaded`.
- Added fallback metadata (`fallback_from_model`, `fallback_reason`) to `image_gen` audit metadata when the retry succeeds.
- Added unit coverage proving Codex overload retries Seedream while preserving the original selected-model call.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/storyboard/test_storyboard_image_generation.py -q` passed: 5 tests.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/storyboard/storyboard_image_generation.py ai-pic-backend/app/services/storyboard/storyboard_image_generation_request.py ai-pic-backend/tests/unit/services/storyboard/test_storyboard_image_generation.py` passed.
- `cd ai-pic-backend && pytest tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py tests/test_timeline_storyboard_grid_api.py::test_timeline_clip_storyboard_creates_generation_task_for_selected_clip_only tests/unit/services/storyboard/test_storyboard_image_generation.py -q` passed: 11 tests.
- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts tests/timelineWorkspaceLayout.test.tsx` passed: 64 tests.
- `cd ai-pic-frontend && npm run lint` passed with 0 errors and 3 existing warnings.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only --diff-filter=ACM) $(git ls-files --others --exclude-standard)` passed.
- `git diff --check` passed.
- Browser validation for the reference-image modal UI was rerun as Playwright fallback because Chrome DevTools MCP failed twice with `HTTP Not Found` from `http://127.0.0.1:9222/json/version`; evidence is recorded in `2026-06-18T08-54-15Z-timeline-reference-image-modal.md`.

## Next Steps

- Re-run the failed clip storyboard generation from the UI. If Codex is still overloaded, the backend should now retry Seedream once instead of failing immediately.
- Track the separate task `6067` duplicate `timeline_revisions` version conflict independently; it is a different failure path from task `6070`.

## Linked Commits

- Pending.
