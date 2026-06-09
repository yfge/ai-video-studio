## User Prompt

分镜/故事板生成入口还是有问题，没有绑定角色参考 图，没有生成的选择！！ 整体链路是 TMD 乱的

commit and push

## Goals

- Make clip-scoped storyboard generation bind the selected role IP/VirtualIP instead of relying only on name matching.
- Expose a visible role IP choice in the selected Timeline video clip production panel.
- Pass the selected role IP IDs through the frontend API request and backend storyboard task payload.
- Keep the deprecated whole-Timeline storyboard entry out of the flow.

## Changes

- Added clip storyboard character context modules that merge StoryCharacter and EpisodeCharacter visual anchors, with episode role bindings taking precedence.
- Added explicit VirtualIP ID resolution from clip metadata and request payload; explicit IDs now win over text/name matches.
- Extended `TimelineClipStoryboardGenerateRequest` and task parameters with `character_virtual_ip_ids`.
- Added episode character lookup to the Timeline workspace and rendered `绑定角色 IP` checkboxes inside the existing clip storyboard reference card.
- Submitted selected role IP IDs from `生成故事板参考图` as `character_virtual_ip_ids`.
- Split backend storyboard context and dispatch helpers to stay inside repository file-size constraints.
- Added focused backend API/unit tests and frontend component tests for role IP binding and request payloads.

## Validation

1. Local checks:

- `rm -f ai-pic-backend/test.db && cd ai-pic-backend && pytest tests/unit/services/storyboard/test_clip_storyboard_context.py tests/unit/services/storyboard/test_clip_storyboard_episode_character_context.py tests/test_timeline_clip_storyboard_context_api.py -q`
  - Passed: 9 tests.
- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts tests/timelineApiEndpoints.test.ts`
  - Passed: 10 tests.
- `cd ai-pic-frontend && npm run lint`
  - Passed with 0 errors and 3 existing warnings.
- `cd ai-pic-frontend && npm run build`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Passed.
- `python -m py_compile <changed backend modules>`
  - Passed.
- `git diff --check`
  - Passed.
- `SKIP=backend-pytest pre-commit run --files <changed files>`
  - Passed for merge-conflict checks, whitespace, ruff, black, isort, prettier, repo docs, repo contracts, ledger enforcement, and frontend lint.
  - `backend-pytest` was skipped because the focused backend pytest command above covers this patch and the repository's broad hook is known to collect unrelated baseline drift.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/episodes/6/workspace?tab=timeline&scriptId=8`
- User path: logged in as the AGENTS.md test account, opened the Timeline tab, selected the current video clip production panel, checked `绑定角色 IP` for `验证快递员-20260609`, and clicked `生成故事板参考图`.
- Chrome DevTools: attempted first; `http://127.0.0.1:9222/json/version` returned HTTP 404, so the run used Playwright with system Google Chrome as fallback.
- Console: only local Next HMR WebSocket 404 errors; no page errors.
- Network: `GET /api/v1/episodes/6/characters?page=1&page_size=20` returned 200; `POST /api/v1/timelines/66/clips/video_scene_001_beat_001_001/storyboard/generate` returned 200.
- Decisive request body: `character_virtual_ip_ids: [82]`.
- Evidence: `artifacts/runs/storyboard-role-ip-fallback-20260609T090506Z/browser_evidence.json`
- Screenshot: `artifacts/runs/storyboard-role-ip-fallback-20260609T090506Z/timeline-role-ip-storyboard-entry.png`

3. Conflict signals and corrections:

- Initial backend fix only inferred role references from clip metadata/name context; this did not provide the missing generation-time selection the user reported.
- Frontend tests caught a render loop from a non-stable default `episodeCharacters = []`; fixed with a stable empty array and an equality guard.
- Repo contract check caught an oversized unit test file; split episode-character storyboard coverage into a dedicated test module.

## Next Steps

- Real image quality and panel-to-video selection should be verified after the async storyboard worker produces a panel image.
- `pre-commit run --all-files` and `./docker/build_prod_images.sh` were not run in this scoped commit; use the targeted validation above for this patch.

## Linked Commits

- Pending.
