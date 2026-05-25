---
id: 2026-05-25T10-07-52Z-timeline-provider-rework-ui
date: "2026-05-25T10:07:52Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, timeline, media-assets, rework, browser]
related_paths:
  - ai-pic-frontend/src/components/features/episode/TimelineClipAssetAuditPanel.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx
  - ai-pic-frontend/src/utils/api/endpoints/timeline.endpoints.ts
  - ai-pic-frontend/src/utils/api/types/timeline.types.ts
  - ai-pic-frontend/tests/timelineClipReworkControls.test.ts
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/exec-plans/active/timeline-main-chain-optimization.md
  - docs/exec-plans/active/timeline-main-chain.md
  - tasks.md
summary: "Wire operator provider video rework controls"
---

## User Prompt

- “按项目规范，依次完成对应计划，保证原子性提交”
- “connit 然后继续”
- “你可以使用chrome mcp”
- “使用你的内置浏览器”

## Goals

- Continue Phase 5 after backend provider-backed video rework queueing landed.
- Add the operator UI entry for selected video clip re-cut/re-render requests.
- Use the Codex built-in Browser for UI validation, not Chrome.
- Keep this commit scoped to the operator provider rework entry; do not claim
  render/export automatic orchestration.

## Changes

- Added `TimelineClipProviderReworkControls` for selected Timeline video clips.
  Operators can choose re-cut or re-render, enter prompt/model/duration/ratio
  details, and submit a provider-backed video rework task.
- Added frontend request/response types and
  `timelineAPI.queueTimelineClipVideoRework` for
  `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework/video`.
- Mounted the provider controls inside the selected clip asset audit panel below
  the existing media-asset replacement controls.
- Added focused frontend tests for provider payload construction and native
  Timeline video clip detection.
- Updated `tasks.md` and active execution plans to mark operator provider rework
  entry complete while leaving render/export orchestration and production sample
  validation pending.

## Validation

- `cd ai-pic-frontend && npm run test`
  - Result: passed, 19 tests.
- `cd ai-pic-frontend && npm run lint`
  - Result: passed with 0 errors and 18 existing warnings.
- Codex built-in Browser validation opened
  `http://localhost:8089/episodes/133/workspace?tab=timeline&scriptId=117`,
  logged in with the repository test account, selected a Timeline video clip,
  filled the provider rework form, and confirmed the `生成重做视频` button was
  visible and enabled.
- Browser evidence:
  `artifacts/runs/frontend-provider-rework-controls-iab-20260525T100147Z/browser-validation.json`
  and
  `artifacts/runs/frontend-provider-rework-controls-iab-20260525T100147Z/timeline-provider-rework-controls.png`.
- Browser validation did not submit the provider form to avoid queueing a real
  provider task in the local development environment. Backend queue behavior is
  covered by the previous backend API/service tests.

## Next Steps

- Wire successful provider rework output into the relevant render/export queue.
- Add stronger export idempotency coverage around rework-triggered renders.
- Continue legacy stability cleanup after the rework/render boundary is covered.

## Linked Commits

- Pending
