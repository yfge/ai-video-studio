---
id: 2026-06-08T08-26-20Z-dialogue-facade-dead-code-cleanup
date: "2026-06-08T08:26:20Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - backend
  - dead-code
  - audio
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/audio/dialogue_service_compat.py
  - ai-pic-backend/app/services/audio/dialogue_service_text_compat.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_request.py
  - ai-pic-backend/tests/unit/test_audio_timeline_storyboard.py
  - scripts/contract_audit_core.py
summary: Removed the dead dialogue-audio compatibility facade and stale Volcengine private compatibility helpers.
---

## User Prompt

Continue goal: 清理项目的死代码，直到没有

## Goals

- Continue removing code that current repository references prove is dead.
- Avoid treating legacy naming alone as proof; preserve compatibility entry points that are still in the live import chain.
- Keep unrelated episode/rework frontend worktree changes out of this batch.

## Changes

- Deleted `app.services.dialogue_audio_service`, which no production code imported after the audio services had moved under `app.services.audio`.
- Deleted `audio.dialogue_service_compat` and `audio.dialogue_service_text_compat`; they were only used by the removed facade.
- Moved the surviving audio timeline/storyboard tests to canonical modules and renamed the stale test file to `test_audio_timeline_storyboard.py`.
- Removed `dialogue_audio_service.py` from contract-audit baseline exemptions and legacy-reference patterns.
- Removed Volcengine private compatibility helpers `_build_prompt_with_flags`, `_contains_flag`, and `_normalize_resolution_flag`; internal code uses `build_video_request` directly.
- Investigated `task_worker.py` re-export cleanup, then reverted that exploratory change because removing those re-exports requires first splitting existing route handlers that currently fail changed-file contracts.

## Validation

- Passed: `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/unit/test_audio_timeline_storyboard.py ai-pic-backend/tests/unit/services/audio/test_dialogue_processor.py ai-pic-backend/tests/unit/services/audio/test_audio_emotions.py ai-pic-backend/tests/unit/services/audio/test_audio_generator.py` (`76 passed`).
- Passed: `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/unit/test_volcengine_provider_video.py ai-pic-backend/tests/unit/test_audio_timeline_storyboard.py ai-pic-backend/tests/unit/services/audio/test_dialogue_processor.py ai-pic-backend/tests/unit/services/audio/test_audio_emotions.py ai-pic-backend/tests/unit/services/audio/test_audio_generator.py` (`84 passed`).
- Passed: `ai-pic-backend/.venv/bin/python -m pyflakes ai-pic-backend/app ai-pic-backend/tests ai-pic-backend/scripts scripts`.
- Passed: `ai-pic-backend/.venv/bin/python -m compileall -q ai-pic-backend/app ai-pic-backend/tests/unit/test_audio_timeline_storyboard.py scripts`.
- Passed: `python scripts/check_repo_docs.py`.
- Passed: `python scripts/check_repo_contracts.py --mode audit` (`checked_files=1354` after deleting three backend files).
- Passed: `python scripts/check_repo_contracts.py --mode diff <changed backend files>`.
- Passed: `cd ai-pic-frontend && npm exec -- tsc --noEmit --noUnusedLocals --noUnusedParameters --pretty false`.
- Passed: `cd ai-pic-frontend && npm run lint` (0 errors, 4 existing warnings).
- Passed with documented skip: `SKIP=backend-pytest pre-commit run --files $(git diff --cached --name-only --diff-filter=ACMR)`.
- Failed during exploratory task-worker re-export migration, then reverted: `python scripts/check_repo_contracts.py --mode diff ...` reported existing route-handler violations in touched `virtual_ip_images/generation.py`, `virtual_ip_images/variants.py`, and `story_structure/environment_variants.py`.

## Next Steps

- Continue with candidates that are provably outside the live import chain.
- Handle `task_worker.py` re-export cleanup only after the affected endpoint handlers are split below contract limits.

## Linked Commits

- Pending.
