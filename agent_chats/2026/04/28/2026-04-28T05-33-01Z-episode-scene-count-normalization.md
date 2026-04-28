---
id: 2026-04-28T05-33-01Z-episode-scene-count-normalization
date: 2026-04-28T05:33:01Z
participants:
  - user
  - codex
models:
  - GPT-5
tags:
  - backend
  - episode-generation
  - scene-normalization
related_paths:
  - ai-pic-backend/app/services/episode/episode_scene_normalization.py
  - ai-pic-backend/app/services/episode/episode_generation_persistence.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/helpers.py
  - ai-pic-backend/app/repositories/episode_repository.py
  - ai-pic-backend/app/prompts/templates/episode_from_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_generation.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_film.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_tv_series.txt
  - ai-pic-backend/tests/unit/test_episode_scene_fallback.py
  - ai-pic-backend/tests/unit/services/episode/test_episode_generation_persistence.py
summary: Fix generated episodes collapsing scenes to 1 by centralizing scene normalization and tightening prompt examples.
---

## User Prompt

现在成生剧集以后  场景都为1

## Goals

- Prevent generated episode plans from persisting all scenes as `scene_number = 1`.
- Prevent underreported `scene_count = 1` from truncating usable scene or plot-point structure.
- Keep sync and async episode generation on the same scene normalization behavior.
- Reduce prompt examples that encouraged one-scene output.

## Changes

- Added `episode_scene_normalization.ensure_scenes` in the episode service layer.
- Normalization now:
  - filters empty scene objects,
  - infers minimum scene count from valid scenes and plot points,
  - pads missing scenes from plot points before generic placeholders,
  - rewrites scene numbers to a continuous `1..N` sequence,
  - writes cleaned `scenes` and `scene_count` back to the episode payload.
- Re-exported the normalizer through episode helpers for existing callers.
- Updated synchronous episode persistence to call the same normalizer before saving `Episode.scene_count` and `extra_metadata.scenes`.
- Added `episode_repository` to move touched helper/persistence direct SQLAlchemy lookups behind repository functions.
- Updated episode generation prompt examples so `scene_count` equals `scenes.length` and scene numbers are continuous, including short-drama, TV-series, film, and outline-based templates.
- Added regression tests for underreported `scene_count=1`, duplicate scene numbers, and synchronous persistence normalization.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/test_episode_scene_fallback.py tests/unit/services/episode/test_episode_generation_persistence.py -q` -> pass, 5 tests passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> pass.
- `python scripts/check_repo_docs.py` -> pass.
- `cd ai-pic-backend && python run_tests.py quick` -> failed during dependency installation before tests ran. Pip could not resolve `pydantic==2.5.0` with `langchain-core==0.2.43` on the current Python 3.13 environment.

2. Browser or MCP validation:

- Run id: `2026-04-28T05-33-01Z-episode-scene-count`.
- `python scripts/harness/doctor.py --run-id 2026-04-28T05-33-01Z-episode-scene-count` -> failed.
- Evidence: `api_health` was OK at `http://localhost:8000/health`; `frontend_port` was false for `http://localhost:3000`; nginx login at `http://localhost:8089/login` timed out.
- Result: real browser E2E was not run because the frontend entrypoint was unavailable in the current local harness state.

3. Conflict signals and corrections:

- Initial assumption: the issue might be only a displayed scene count.
- Contradicting evidence: existing normalization accepted `scene_count=1`, could truncate to one scene, and did not fix duplicate scene numbers.
- Reproduction and fix: added unit coverage for both `scene_count=1` with four plot points and three generated scenes all numbered `1`; normalizer now expands and renumbers.
- Final verified state: targeted backend tests and repository diff contracts pass.

## Next Steps

- Run full browser generation flow once the frontend is available on port 3000 or nginx login is responsive.
- Re-run `python run_tests.py quick` in a Python environment whose pinned dependencies resolve.

## Linked Commits

- Not committed yet.
