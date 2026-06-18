## User Prompt

PLEASE IMPLEMENT THIS PLAN:

Timeline Reference Image Modal Plan. Replace inline IP/environment thumbnail walls in the selected-clip production panel with compact summaries plus modal pickers for IP 图 and 环境图. Keep existing URL-array payloads unchanged, preserve default first-image selection, update timeline tests, run validation, and add/update the required ledger entry.

## Goals

- Replace inline reference image walls with compact selected-count summaries and up to three selected previews.
- Add modal pickers for IP 图 and 环境图 with staged draft selection, cancel discard, clear, and apply behavior.
- Group IP images by selected VirtualIP and inferred category; group environment images in the current environment picker.
- Preserve existing request payload fields for storyboard, keyframe, and video generation.
- Validate with focused tests, lint/contracts/docs checks, and browser evidence on episode 49.

## Changes

- Added `TimelineClipReferenceImagePickerModal` as a reusable modal picker with draft selection state, checkbox-style image tile buttons, all/clear/apply controls, and cancel/backdrop/ESC discard behavior.
- Added `TimelineClipReferenceImagePickerModel` to build grouped IP and environment picker sections from existing option labels and episode character data.
- Reworked `TimelineClipStoryboardReferenceImages` so IP 图 and 环境图 render inline as compact summaries with selected preview thumbnails, picker buttons, and inline clear actions.
- Updated `TimelineClipStoryboardReferenceCard` to pass episode character labels into the reference image selector.
- Updated timeline control and layout tests to open modals, toggle selections, verify cancel and clear behavior, and assert unchanged payload/shared-context behavior.

## Validation

- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts tests/timelineWorkspaceLayout.test.tsx`
  - Passed: 63 tests.
- `cd ai-pic-frontend && npm run lint`
  - Passed with existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only --diff-filter=ACM) $(git ls-files --others --exclude-standard)`
  - Passed after splitting modal grouping helpers out of the UI file.
- `python scripts/check_repo_contracts.py --mode audit`
  - Passed.
- `python scripts/check_repo_docs.py`
  - Passed.
- `git diff --check`
  - Passed.
- Full `cd ai-pic-frontend && npm run test` was attempted, but stopped after unrelated existing dirty/untracked tests failed:
  - `tests/operatorShellNavIcon.test.tsx` failed.
  - `tests/productionCanvasBoard.test.tsx` could not resolve `../src/components/features/canvas/ProductionCanvasBoard`.
  - The updated timeline modal suites passed in that full run before interruption.
- Browser validation:
  - Chrome DevTools retry failed with `Could not connect to Chrome via http://127.0.0.1:9222/json/version: HTTP Not Found`.
  - Fallback used Playwright with system Chrome against `http://localhost:3100/episodes/49/workspace?tab=timeline`.
  - Logged in with the repository test account and validated episode 49 timeline selected clip `video_scene_90_beat_3991_001`.
  - Evidence stored under `artifacts/runs/20260618T085355Z-timeline-reference-modal/`.
  - Verified inline panel has compact picker controls, no inline IP tile wall, one selected IP preview, and one selected environment preview.
  - Verified IP modal opens with 44 grouped IP tile buttons, including `老拐` and `portrait`.
  - Verified environment modal opens with 2 environment tile buttons.
  - Verified cancelling a staged IP deselection preserves `IP 图：1 张`.
  - Verified applying selection preserves shared context `角色 IP：老拐 / IP 图：1 张 / 环境图：1 张`.
  - Observed only local `/uploads/*.png` 404 image responses; no non-image API failures were recorded.
- Additional browser fallback validation after the Codex overload follow-up:
  - Chrome DevTools failed twice with `HTTP Not Found` from `http://127.0.0.1:9222/json/version`; fallback used Playwright with system Chrome.
  - Entry URL: `http://127.0.0.1:3100/episodes/49/workspace?tab=timeline&clipId=video_scene_91_beat_4003_013`.
  - The app normalized the selected clip URL to `video_scene_90_beat_3991_001`; DB inspection confirmed timeline `69` version `4` still contains `video_scene_91_beat_4003_013`, so this run validates the modal UI path on the current selected production panel rather than the target clip-specific backend failure.
  - Evidence stored under `artifacts/runs/2026-06-18T09-39-00Z-timeline-reference-modal-playwright/`.
  - Verified inline production panel had 3 images before opening pickers, not the full 44-image IP wall.
  - Verified `选择 IP 图` opened a modal with `老拐`, `portrait`, `full_body`, `清空`, `应用选择`, and 44 modal images.
  - Verified `选择环境图` opened a modal with `清空`, `应用选择`, and 2 modal images.
  - API requests in the path were 200; one non-API local image response returned 404 for `/uploads/ce7080ca7efd47db990397b1541a0b23.png`.

## Next Steps

- Resolve the unrelated dirty test failures before treating the full frontend test suite as clean.
- Restore or serve the missing local `/uploads/*.png` assets if thumbnail image 404s matter for manual review on this workstation.

## Linked Commits

Pending commit.
