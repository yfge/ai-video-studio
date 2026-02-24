---
id: 2026-02-24T07-54-24Z-storyboard-deprecation-ui-guidance
date: 2026-02-24T07:54:24Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [frontend, storyboard, api, ux]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api/endpoints/script/audio.endpoints.ts
  - tasks.md
summary: "Added frontend deprecation guidance for step-by-step storyboard sync entry and quick navigation to timeline one-click pipeline."
---

## User Prompt

继续

## Goals

- Continue the deprecation rollout by making the frontend explicitly guide operators away from step-by-step endpoints.
- Keep existing functionality available while steering users to timeline one-click pipeline.
- Finish with lint + browser verification and a traceable ledger entry.

## Changes

- Updated `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`:
  - Added deprecation guidance banner in the "对白时间轴（场景）" area.
  - Banner text includes concrete sunset date `2026-12-31`.
  - Added `前往时间轴页` button that navigates to workspace timeline tab and injects `autoTimelinePipeline` query param to auto-trigger one-click pipeline.
  - Updated old step endpoint success toast to include migration guidance toward one-click pipeline.
- Updated `ai-pic-frontend/src/utils/api/endpoints/script/audio.endpoints.ts`:
  - Added `@deprecated` JSDoc on:
    - `generateSceneDialogueAudioAsync`
    - `generateAudioTimelineAsync`
    - `generateStoryboardFromAudioTimelineAsync`
  - Recommendation points to `generateTimelinePipelineAsync`.
- Updated `tasks.md`:
  - Marked frontend deprecate-guidance task complete under P0 `huobao-drama` gap closure section.

## Validation

- `pre-commit run --files 'ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx' ai-pic-frontend/src/utils/api/endpoints/script/audio.endpoints.ts tasks.md`
  - passed, including `frontend lint` hook.
- Chrome E2E (lite stack):
  - Logged in at `http://localhost:8089/login` with `geyunfei / Gyf@845261`.
  - Opened `http://localhost:8089/episodes/1/storyboard`.
  - Confirmed banner text rendered with sunset date and `前往时间轴页` CTA.
  - Clicked `前往时间轴页`, navigated to workspace timeline URL and auto-triggered one-click pipeline.
  - Verified in UI that timeline pipeline task was created (`task_id=6`) and by API that task type is `timeline_pipeline`.
- Conflict handling / correction record:
  - Auto-triggered task ended as `failed` with `error_message=no_scenes_found` in this local lite dataset.
  - I treated this as environment/data precondition mismatch (missing normalized scenes), not as proof that the UI flow failed, and validated the actual goal (migration guidance + navigation + trigger) via real browser and task API.

## Next Steps

- If needed, add the same deprecation guidance in any remaining UI surfaces that still expose step-by-step calls.
- Consider showing backend deprecation headers (`Deprecation/Sunset`) in frontend toast for runtime visibility.

## Linked Commits

- (pending)
