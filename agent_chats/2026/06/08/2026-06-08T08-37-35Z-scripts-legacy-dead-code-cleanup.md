---
id: 2026-06-08T08-37-35Z-scripts-legacy-dead-code-cleanup
date: "2026-06-08T08:37:35Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - backend
  - scripts
  - dead-code
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/media.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_processor.py
  - ai-pic-backend/app/services/task_worker_storyboard_media.py
  - scripts/contract_audit_core.py
  - docs/architecture/contracts.md
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/design/image-generation-unification.md
summary: Removed the dead scripts legacy compatibility router and updated docs/contracts to the current split router.
---

## User Prompt

`/goal 清理系统中旧的死代码`

`commit and push`

## Goals

- Remove a provably unused backend compatibility router after the current split `/scripts` package became the runtime route mount.
- Keep repo contracts and current design docs aligned with the removed code so future dead-code scans do not rediscover stale paths.
- Commit and push only this cleanup batch while leaving unrelated workspace changes untouched.

## Changes

- Deleted `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`.
- Removed `scripts_legacy` from the legacy-reference contract scan rule because the file no longer exists.
- Updated architecture contracts and active/design docs to point at the current split script router, storyboard media endpoint, storyboard image worker, and focused audio services instead of retired compatibility files.

## Validation

- `rg -n "scripts_legacy|dialogue_audio_service|dialogue_service_compat|dialogue_service_text_compat" docs scripts ai-pic-backend/app ai-pic-backend/tests -g '*.md' -g '*.py'` only reports the untouched oversized `ai-pic-backend/tests/test_api.py` comment.
- `ai-pic-backend/.venv/bin/python -m pyflakes ai-pic-backend/app ai-pic-backend/tests ai-pic-backend/scripts scripts`
- `ai-pic-backend/.venv/bin/python -m compileall -q ai-pic-backend/app scripts`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode audit`
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py scripts/contract_audit_core.py docs/architecture/contracts.md docs/exec-plans/active/main-chain-commercial-readiness.md docs/design/image-generation-unification.md docs/design/script-beat-contract.md docs/exec-plans/active/timeline-main-chain-optimization.md docs/design/duration-orchestrator-agent.md`
- `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/unit/test_scripts_storyboard_route_registration.py ai-pic-backend/tests/scripts/test_script_prompt_preview_api.py ai-pic-backend/tests/scripts/test_script_soft_delete_api.py ai-pic-backend/tests/scripts/test_script_story_structure_sync.py ai-pic-backend/tests/scripts/test_script_regeneration_soft_delete.py ai-pic-backend/tests/unit/test_storyboard_image_task_reference_requirement.py ai-pic-backend/tests/unit/test_storyboard_image_task_image_gen_persistence.py`
- `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/test_api.py::TestScriptAPI::test_export_script`

## Next Steps

- Continue iterative dead-code review from actual imports/call chains. The remaining `scripts_legacy` text is an old comment inside an oversized baseline test file and was intentionally not touched in this commit.

## Linked Commits

- This commit: `chore(backend): remove dead scripts legacy router`.
