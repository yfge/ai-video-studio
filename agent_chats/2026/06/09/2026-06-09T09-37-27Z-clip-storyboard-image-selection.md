---
id: 2026-06-09T09-37-27Z-clip-storyboard-image-selection
date: "2026-06-09T09:37:27Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, backend, storyboard, timeline]
related_paths:
  - ai-pic-backend/app/schemas/timeline.py
  - ai-pic-backend/app/services/storyboard/clip_storyboard_context.py
  - ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_service.py
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx
  - ai-pic-frontend/tests/timelineClipReworkControls.test.ts
summary: "Added selectable IP and environment reference thumbnails for clip storyboard generation and prioritized selected URLs in reference_images."
---

## User Prompt

分镜/故事板生成入口还是有问题，没有绑定角色参考 图，没有生成的选择！！ 整体链路是 TMD 乱的

commit and push

需要可以选择 IP 图，环境图，做到了么？

## Goals

- Add explicit IP image thumbnail selection to the clip storyboard reference card.
- Add explicit environment image thumbnail selection to the clip storyboard reference card.
- Send selected image URLs through the frontend API client and backend request schema.
- Prioritize selected IP/environment images in generated task `reference_images`.

## Changes

- Added `character_reference_images` and `environment_reference_images` to clip storyboard generation requests.
- Merged selected IP images, selected environment images, manual references, auto character anchors, and auto environment references in deterministic priority order.
- Added frontend thumbnail selectors for bound role IP images and the selected scene environment images.
- Loaded role images from episode character resources and loaded full environment details when the environment list only contains summary rows without `reference_images`.
- Split the clip rework/storyboard UI into smaller files to stay within repository file-size contracts.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_clip_storyboard_context_api.py tests/unit/services/storyboard/test_clip_storyboard_episode_character_context.py -q`
  - Result: passed, 8 tests.
- `cd ai-pic-frontend && npm run lint`
  - Result: passed with existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run test -- tests/timelineClipReworkControls.test.ts`
  - Result: passed, 45 tests.
- `cd ai-pic-frontend && npm run build`
  - Result: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Result: passed.
- `pre-commit run --files <changed files>`
  - Result: black/prettier formatted files; `backend-pytest` failed while collecting unrelated full-backend tests with existing import errors for `_BEAT_CONTRACT_MAX_TOKENS`, `structured_script_score`, and `STRUCTURED_SCORE_PASS`.
- `SKIP=backend-pytest pre-commit run --files <changed files>`
  - Result: passed; backend coverage for this change is covered by the focused pytest command above.
- Browser validation:
  - Chrome DevTools MCP failed because `http://127.0.0.1:9222/json/version` returned HTTP Not Found.
  - Fallback used Playwright with system Google Chrome.
  - URL: `http://localhost:8089/episodes/6/workspace?tab=timeline&scriptId=8`.
  - Evidence: `artifacts/runs/storyboard-image-selection-20260609T0928Z/browser_evidence.json`.
  - Result: rendered 1 IP thumbnail and 16 environment thumbnails, selected one of each, submitted `/storyboard/generate` with `character_reference_images` and `environment_reference_images`.
  - Backend task `6031` persisted `reference_images` with selected IP image first and selected environment image second.

## Next Steps

- None for this fix.

## Linked Commits

- This commit: `fix(storyboard): select clip reference images`
