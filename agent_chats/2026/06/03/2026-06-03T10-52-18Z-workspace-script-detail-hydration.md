---
id: 2026-06-03T10-52-18Z-workspace-script-detail-hydration
date: "2026-06-03T10:52:18Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, episode-workspace, scripts]
related_paths:
  - ai-pic-frontend/src/hooks/useEpisodeDetail.ts
  - ai-pic-frontend/src/hooks/episode/scriptDetailHydration.ts
  - ai-pic-frontend/src/hooks/episode/useSelectedScriptDetailHydration.ts
  - ai-pic-frontend/tests/episodeScriptDetailHydration.test.ts
summary: "Hydrate selected episode workspace script details"
---

## User Prompt

http://localhost:8089/episodes/7de415c975a94c31ac32194e11da2e34/workspace?tab=script&scriptId=131 剧本页为空

## Goals

- Reproduce the empty script workspace path for episode `7de415c975a94c31ac32194e11da2e34` and `scriptId=131`.
- Identify whether the issue is missing data, API response shape, or frontend rendering.
- Restore script dialogue and stage-direction display without expanding backend list payloads.

## Changes

- Found script `131` exists with content, 4 scenes, 23 dialogues, and 15 stage directions.
- Found the workspace loads `/api/v1/scripts/episode/business/...`, which intentionally returns lightweight `ScriptListItemResponse` without `content`, `scenes`, `dialogues`, or `stage_directions`.
- Added selected-script detail hydration so the workspace keeps the lightweight episode script list but fetches `/api/v1/scripts/business/{script_business_id}` for the selected script when details are missing.
- Added pure helpers for detecting lightweight scripts and merging fetched detail into the current scripts list.
- Added unit coverage for lightweight script detection and detail merge behavior.
- Extracted the hydration effect into a focused hook so `useEpisodeDetail.ts` stays under the repository TypeScript file-size limit.

## Validation

- Chrome DevTools MCP could not connect: `127.0.0.1:9222/json/version` returned HTTP 404, so browser validation used Playwright with system Google Chrome.
- DB check: `scriptId=131` has `scenes_len=4`, `dialogues_len=23`, and `directions_len=15`.
- Before fix browser evidence: after login, workspace showed `场景 1 / 0 句 / 暂无对白 / 暂无舞台指令` while the episode script list endpoint returned only lightweight script fields.
- `cd ai-pic-frontend && npm run test -- tests/episodeScriptDetailHydration.test.ts` -> red before helper implementation due missing module; passed after implementation, 30 tests.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/hooks/useEpisodeDetail.ts ai-pic-frontend/src/hooks/episode/scriptDetailHydration.ts ai-pic-frontend/src/hooks/episode/useSelectedScriptDetailHydration.ts ai-pic-frontend/tests/episodeScriptDetailHydration.test.ts` -> passed.
- `cd ai-pic-frontend && npm run lint` -> passed with existing warnings only, 0 errors.
- `python scripts/check_repo_docs.py` -> passed.
- Final Playwright validation at the reported URL: `/api/v1/scripts/episode/business/7de415c975a94c31ac32194e11da2e34` returned 200, `/api/v1/scripts/business/f83f9c1de0c74bc2ad773ddad710c13b` returned 200, page displayed `场景 1 / 4 句` and dialogue `全链路警报？核心素材库被远程删除！`; no material console errors.

## Next Steps

- None for this issue.

## Linked Commits

- Pending.
