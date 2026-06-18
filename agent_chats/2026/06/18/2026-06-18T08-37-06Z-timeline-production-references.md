## User Prompt

/goal 现在从故事到短剧生成全是断的，时间线看不到 IP ，选不了 IP 图 ，环境图也选不了，对白也 TMD 没有

## Goals

- Restore character/dialogue context on Timeline video clips so the selected clip production panel can bind the right IP.
- Fall back from empty episode-local temporary characters to story-level VirtualIP characters.
- Load selectable IP reference images for story-level VirtualIP characters.
- Default old unbound scenes to a usable environment reference when the scene slug clearly matches an existing environment.
- Validate against the real broken episode/task path without claiming unsupported Chrome DevTools evidence.

## Changes

- Backend Timeline spec builder now carries `speaker_name`, `characters_involved`, `dialogue_action`, and `dialogue_emotion` onto generated clips, including video clips.
- Added frontend clip character-context extraction for explicit VirtualIP IDs and character names across native clip metadata, `source_refs`, `source`, shot-plan metadata, and bound context.
- Timeline production characters now merge episode-local characters with story-level characters via episode -> story fallback, deduped by VirtualIP ID.
- Story-level character image loading now fetches VirtualIP detail and builds selectable image options from `images`, `default_avatar_url`, and style reference images.
- Old native Timeline drafts now enrich selected video clip metadata from matching audio timeline beats by numeric or string `beat_id`, so existing clips can recover speaker/character context without regeneration.
- Added conservative environment inference for unbound scenes. For episode 49 scene `INT. 老拐的客厅 - DAY`, the UI infers `老拐的家` for local reference selection without saving it unless the user explicitly saves.
- Added regression coverage for backend clip context propagation, frontend character-name default binding, story-IP fallback with VirtualIP images, old-draft audio-beat enrichment, and inferred environment reference submission.

## Validation

- Backend focused:
  - `cd ai-pic-backend && pytest tests/test_timeline_import_service.py::test_import_audio_timeline_creates_timeline_spec_tracks -q` -> passed.
  - `cd ai-pic-backend && pytest tests/test_timeline_import_service.py tests/test_timeline_shot_plan_api.py tests/test_timeline_clip_storyboard_context_api.py tests/test_timeline_clip_video_rework_context_api.py -q` -> `14 passed`.
- Frontend focused:
  - `cd ai-pic-frontend && npx tsx --test tests/timelineWorkspaceHelpers.test.ts tests/timelineClipReworkControls.test.ts tests/timelineWorkspaceLayout.test.tsx` -> `80 passed`.
  - `cd ai-pic-frontend && npm run lint` -> exit 0 with 3 existing warnings in unrelated files/config.
- Repo checks:
  - `python scripts/check_repo_docs.py` -> ok.
  - `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only --diff-filter=ACM)` -> ok.
  - `python scripts/check_repo_contracts.py --mode audit` -> ok.
  - `git diff --check` -> ok.
- Browser evidence:
  - Preferred Chrome DevTools failed before navigation: `Could not connect to Chrome... http://127.0.0.1:9222/json/version: HTTP Not Found`.
  - Fallback used Playwright with system Chrome executable against `http://localhost:3100/episodes/49/workspace?tab=timeline`.
  - Real page after login resolved to `/episodes/49/workspace?tab=timeline&scriptId=30&clipId=video_scene_90_beat_3991_001`.
  - Assertion result: `laoguaiChecked=true`, `agaierChecked=false`, shared context `角色 IP：老拐 / IP 图：1 张 / 环境图：1 张`, inferred environment `老拐的家`, `failedRequestCount=0`.
- Full frontend suite note:
  - `cd ai-pic-frontend && npm run test` was interrupted with exit 130 after hanging in `tests/toastProvider.test.tsx`; the timeline/workspace suites had already passed in that run and were rerun successfully as focused validation.

## Next Steps

- Existing task `6065` still has backend task status `failed` with `timeline shot plan JSON invalid`; this change fixes the Timeline reference chain and old-draft UI recovery, but does not rerun the failed AI pipeline task.
- Scene environment inference is intentionally local/read-only until the operator clicks save.

## Linked Commits

- Pending commit.
