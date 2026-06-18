---
id: 2026-06-18T06-15-25Z-timeline-clip-chain
date: "2026-06-18T06:15:25Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - timeline
  - frontend
  - clip-production
related_paths:
  - ai-pic-frontend/src/components/features/episode/ClipProductionActionShell.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineClipSupportPanel.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipGenerationChain.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipProductionReadiness.ts
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCards.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipVideoReworkCard.tsx
  - ai-pic-frontend/tests/timelineClipReworkControls.test.ts
  - ai-pic-frontend/tests/timelineWorkspaceLayout.test.tsx
summary: Clarify the selected Timeline clip image-to-video chain and gate video generation on required image assets.
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: 时间轴生图/生视频链路清晰化计划。

## Goals

- Make the selected Timeline video clip production path explicit:
  `选参考/绑定 -> 生图：分镜图 -> 生图：首尾帧 -> 生视频：片段视频`.
- Require both the clip storyboard sheet and start/end keyframes before video generation can be submitted.
- Keep public backend APIs and provider behavior unchanged.

## Changes

- Added clip production readiness helpers for storyboard, keyframe, and video gate state.
- Added a visible selected-clip generation chain above the existing reference and action controls.
- Changed mobile ordering so storyboard, keyframes, and video stay in production order.
- Disabled video submission until both clip storyboard and start/end keyframes are ready, including submit-handler protection.
- Kept selected-clip script navigation visible outside the collapsed support menu so the script context is not hidden by the production chain.
- Added focused frontend regression coverage for the visible chain, hard video gate, manual-reference non-bypass, mobile order, and visible script navigation.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts tests/timelineWorkspaceLayout.test.tsx` -> pass, 59 tests / 0 failures.
- `cd ai-pic-frontend && npm run test` -> interrupted after the runner stayed active with no output for 60 seconds after completing the visible suites; output before interrupt included the changed Timeline suites passing and no reported failures.
- `cd ai-pic-frontend && npm run lint` -> pass with 0 errors and 3 existing warnings (`eslint.config.mjs` anonymous default export, two existing `<img>` warnings).
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff $(git status --short | awk '{print $2}')` -> pass.
- `git diff --check` -> pass.
- Commit-time recheck before split commit:
  - `python scripts/check_repo_docs.py` -> pass.
  - `python scripts/check_repo_contracts.py --mode diff <backend/frontend/ledger changed paths>` -> pass.
  - `git diff --check` -> pass.
  - `cd ai-pic-frontend && npm run lint` -> pass with 0 errors and the same 3 existing warnings.
  - `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts tests/timelineWorkspaceLayout.test.tsx` -> pass, 59 tests / 0 failures.
  - `pre-commit run --all-files` -> failed on existing all-repo issues (`ruff` historical files and pytest collection error in `tests/unit/services/ai/test_scripts_ai_manager.py`); unrelated EOF hook edits were restored before staging.
  - `./docker/build_prod_images.sh` -> pass; pushed backend and frontend production images with tag `068996e3`.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/episodes/124/workspace?tab=timeline`
- Run id: `timeline-clip-chain-auth-20260618T061525Z`
- User path: authenticated browser harness opened episode `124` Timeline workspace and landed on `http://localhost:8089/episodes/124/workspace?tab=timeline&scriptId=127`.
- Console: only React DevTools info and HMR connected logs.
- Network: key workspace/API requests returned 200, including `/api/v1/episodes/124`, `/api/v1/scripts/episode/124`, `/api/v1/episodes/124/timelines`, `/api/v1/episodes/124/characters`, `/api/v1/ai/models/available?model_type=video`, and `/api/v1/story-structure/environments`.
- Result: pass via Playwright fallback. Chrome DevTools MCP first timed out at `http://127.0.0.1:9222`, so browser status is recorded as degraded rather than Chrome-verified.

3. Conflict signals and corrections:

- Initial browser run without explicit credentials redirected to login and was not treated as sufficient Timeline workspace proof.
- Re-ran with the current `AGENTS.md` test account and verified the authenticated Timeline workspace path.

## Next Steps

- None planned beyond final validation.

## Linked Commits

- This commit.
