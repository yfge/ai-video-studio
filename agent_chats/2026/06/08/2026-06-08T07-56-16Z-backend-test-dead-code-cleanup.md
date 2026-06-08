---
id: 2026-06-08T07-56-16Z-backend-test-dead-code-cleanup
date: "2026-06-08T07:56:16Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - backend
  - tests
  - dead-code
related_paths:
  - ai-pic-backend/tests/api/test_role_management.py
  - ai-pic-backend/tests/api/test_user_approval_modal.py
  - ai-pic-backend/tests/api/test_user_details_modal.py
  - ai-pic-backend/tests/fixtures/db.py
  - ai-pic-backend/tests/integration/test_readiness_api.py
  - ai-pic-backend/tests/integration/test_validator_integration.py
  - ai-pic-backend/tests/scripts/test_prototype_story_structure_migration.py
  - ai-pic-backend/tests/services/test_diagnostic_service.py
  - ai-pic-backend/tests/test_fastapi_full_flow.py
  - ai-pic-backend/tests/test_migration_system.py
  - ai-pic-backend/tests/test_models.py
  - ai-pic-backend/tests/test_simple.py
  - ai-pic-backend/tests/test_user_management.py
  - ai-pic-backend/tests/unit/services/agent_core/test_quality_loop.py
  - ai-pic-backend/tests/unit/services/agent_core/test_react_agent_base.py
  - ai-pic-backend/tests/unit/services/agents/test_dialogue_audio_agent.py
  - ai-pic-backend/tests/unit/services/continuity/test_ledger_compressor.py
  - ai-pic-backend/tests/unit/services/image/test_image_persistence.py
  - ai-pic-backend/tests/unit/services/readiness/test_episode_readiness.py
  - ai-pic-backend/tests/unit/services/readiness/test_story_quick_fix.py
  - ai-pic-backend/tests/unit/services/readiness/test_story_readiness.py
  - ai-pic-backend/tests/unit/services/render/test_episode_render_service.py
  - ai-pic-backend/tests/unit/services/storyboard/pipeline/test_storyboard_pipeline.py
  - ai-pic-backend/tests/unit/services/storyboard/sync/test_script_structure_sync.py
  - ai-pic-backend/tests/unit/services/storyboard/test_frame_duration_splitter.py
  - ai-pic-backend/tests/unit/services/storyboard/validators/test_consistency_validator.py
  - ai-pic-backend/tests/unit/services/storyboard/validators/test_timeline_validator.py
  - ai-pic-backend/tests/unit/services/storyboard/validators/test_visual_continuity_validator.py
  - ai-pic-backend/tests/unit/services/timeline_agent/test_react_agent.py
  - ai-pic-backend/tests/unit/services/validators/test_character_consistency_validator.py
  - ai-pic-backend/tests/unit/services/video/test_video_capabilities.py
  - ai-pic-backend/tests/unit/test_database.py
  - ai-pic-backend/tests/unit/test_episode_character_service.py
  - ai-pic-backend/tests/unit/test_virtual_ip_unique_name.py
summary: Removed unused imports and locals from tracked backend tests after extending the dead-code audit to the test tree.
---

## User Prompt

Continue goal: 清理项目的死代码，直到没有

## Goals

- Extend the dead-code scan beyond backend app code into tracked backend tests and scripts.
- Keep current unrelated episode/rework frontend worktree changes out of this batch.
- Avoid deleting compatibility wrappers unless repository call-chain evidence proves they are no longer intentional.

## Changes

- Removed unused imports from backend unit, integration, service, and model tests.
- Removed unused local variables where the value was not part of the assertion.
- Replaced side-effect-only `app.models` imports in test fixtures with explicit `import_module("app.models")`.
- Kept Selenium/live API scripts behavior unchanged; only removed unused wait return bindings.
- Replaced bare `except` blocks in touched Selenium scripts with `except Exception` to satisfy the changed-file lint gate.
- Verified `scripts_legacy.py` is no longer in the main route chain, but left it in place because repository notes still identify it as an intentional compatibility wrapper.

## Validation

- Passed: `git ls-files 'ai-pic-backend/tests/**/*.py' 'ai-pic-backend/tests/*.py' 'scripts/**/*.py' 'scripts/*.py' | xargs ai-pic-backend/.venv/bin/python -m pyflakes`.
- Passed: `ai-pic-backend/.venv/bin/python -m compileall -q ai-pic-backend/tests scripts`.
- Passed: `.venv/bin/python -m pytest <changed pytest files except Selenium/live API scripts> -q` (`539 passed`, `8 skipped`, warnings only).
- Passed: `cd ai-pic-frontend && npm exec -- tsc --noEmit --noUnusedLocals --noUnusedParameters --pretty false`.
- Passed: `cd ai-pic-frontend && npm run lint` (0 errors, 4 existing warnings).
- Passed: `pre-commit run ruff --files <changed backend test files>`.
- Passed: `pre-commit run black --files <changed backend test files>`.
- Passed: `pre-commit run isort --files <changed backend test files>`.
- Passed: `pre-commit run prettier --files agent_chats/2026/06/08/2026-06-08T07-56-16Z-backend-test-dead-code-cleanup.md`.
- Passed: `pre-commit run check-merge-conflict --files ...`, `pre-commit run trailing-whitespace --files ...`, and `pre-commit run end-of-file-fixer --files ...`.
- Passed: `python scripts/check_repo_docs.py`.
- Passed with documented skips: `SKIP=repo-contracts,backend-pytest pre-commit run --files $(git diff --cached --name-only --diff-filter=ACMR)`.
- Expected baseline failure: `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only -- ai-pic-backend/tests agent_chats/2026/06/08/2026-06-08T07-56-16Z-backend-test-dead-code-cleanup.md)` reports existing oversized test files touched by this dead-code cleanup.

## Next Steps

- Continue searching for evidence-backed dead files or compatibility wrappers that can be safely retired.

## Linked Commits

- Pending.
