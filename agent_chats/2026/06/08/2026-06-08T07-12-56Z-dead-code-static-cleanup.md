---
id: 2026-06-08T07-12-56Z-dead-code-static-cleanup
date: "2026-06-08T07:12:56Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - backend
  - dead-code
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes/helpers.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/regenerate.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_processor.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_refs.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/legacy_generate.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/retrieval.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/task_processors.py
  - ai-pic-backend/app/cli/migration_commands.py
  - ai-pic-backend/app/cli/templates/migration_template.py
  - ai-pic-backend/app/cli/templates/seed_template.py
  - ai-pic-backend/app/core/celery_app.py
  - ai-pic-backend/app/prompts/__init__.py
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/app/services/agent_core/context_spec.py
  - ai-pic-backend/app/services/agent_core/context_specs.py
  - ai-pic-backend/app/services/agent_core/react_agent_base.py
  - ai-pic-backend/app/services/ai/scripts_ai_manager.py
  - ai-pic-backend/app/services/audio/__init__.py
  - ai-pic-backend/app/services/audio/audio_generator.py
  - ai-pic-backend/app/services/audio/scene_fallback_tts.py
  - ai-pic-backend/app/services/audio/scene_tts_phase.py
  - ai-pic-backend/app/services/continuity/ledger_compressor.py
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/duration_orchestrator/agent.py
  - ai-pic-backend/app/services/duration_orchestrator/nodes/assemble_episode.py
  - ai-pic-backend/app/services/episode_character_service.py
  - ai-pic-backend/app/services/providers/volcengine_provider/tts.py
  - ai-pic-backend/app/services/script/character_background_generator.py
  - ai-pic-backend/app/services/script/temporary_character_extractor.py
  - ai-pic-backend/app/services/script_quality/checks.py
  - ai-pic-backend/app/services/script_quality/lint_engine.py
  - ai-pic-backend/app/services/story_agent.py
  - ai-pic-backend/app/services/storyboard/pipeline/storyboard_pipeline.py
  - ai-pic-backend/app/services/storyboard/recovery/incremental_repair.py
  - ai-pic-backend/app/services/storyboard/sync/script_structure_sync.py
  - ai-pic-backend/app/services/storyboard/validators/cinematic_rules_validator.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/services/timeline_agent/agent.py
  - ai-pic-backend/app/services/timeline_agent/react_agent.py
  - ai-pic-backend/app/services/validators/info_gate_validator.py
  - ai-pic-backend/app/services/validators/scene_transition_validator.py
  - ai-pic-backend/app/services/validators/script_quality_validator.py
  - ai-pic-backend/app/services/validators/story_quality_validator.py
  - ai-pic-backend/app/services/video/video_capabilities.py
  - ai-pic-backend/app/utils/story_parser.py
  - ai-pic-backend/tests/unit/services/audio/test_audio_emotions.py
  - scripts/harness/production_quality_script.py
summary: Removed static unused imports, locals, star imports, duplicate CLI names, and unreferenced template files found during the dead-code audit.
---

## User Prompt

Continue goal: 清理项目的死代码，直到没有

## Goals

- Continue reducing dead-code signals from current worktree evidence.
- Avoid mechanical deletion of compatibility exports and Celery registration imports.
- Preserve unrelated episode/rework changes already present in the worktree.

## Changes

- Removed ordinary unused imports and locals reported by pyflakes after inspecting their surrounding context.
- Added the missing `ScriptLintRuleResult` import in `lint_engine.py`, which pyflakes reported as undefined.
- Replaced f-strings without placeholders with plain strings.
- Replaced side-effect-only Celery task imports with an explicit `import_module` registration loop.
- Replaced prompt package star import with explicit exports.
- Renamed duplicate Click command function names while preserving the external `create` CLI command names.
- Removed unreferenced CLI template files after repository search confirmed no live code references them.
- Moved TTS emotion imports to `audio_emotions` while preserving historical compatibility surfaces.

## Validation

- Passed: `ai-pic-backend/.venv/bin/python -m pyflakes ai-pic-backend/app ai-pic-backend/scripts scripts`.
- Passed: `ai-pic-backend/.venv/bin/python -m compileall -q ai-pic-backend/app ai-pic-backend/scripts scripts`.
- Passed: `.venv/bin/python -m pytest tests/test_migration_system.py tests/test_script_quality_lint.py tests/unit/services/audio/test_audio_generator.py tests/unit/services/audio/test_audio_emotions.py tests/unit/services/storyboard/pipeline/test_storyboard_pipeline.py tests/unit/services/storyboard/pipeline/test_storyboard_pipeline_plan_graph.py tests/scripts/test_script_story_structure_sync.py -q` (`83 passed`, warnings only).
- Passed: `python scripts/check_repo_docs.py`.
- Passed: `pre-commit run ruff --files ...`, `pre-commit run black --files ...`, `pre-commit run isort --files ...`, `pre-commit run prettier --files ...`, `pre-commit run check-merge-conflict --files ...`, `pre-commit run trailing-whitespace --files ...`, `pre-commit run end-of-file-fixer --files ...`, and `scripts/check_agent_chats.py`.
- Passed with documented skips: `SKIP=repo-contracts,backend-pytest pre-commit run --files $(git diff --cached --name-only --diff-filter=ACMR)`.
- Expected baseline failure: `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only -- ai-pic-backend scripts)` still reports existing oversized/direct-query/legacy-reference hotspots in touched files; this cleanup does not split those historical hotspots.
- Not completed: full `pre-commit run --files ...` reached the `pytest (backend quick gate)` hook (`pytest tests/unit tests/services tests/scripts`) and stayed silent for several minutes. The matching `.venv/bin/python -m pytest tests/unit tests/services tests/scripts -q` command also stayed silent for several minutes and was stopped. Focused backend tests above cover the changed migration, script-quality, audio, storyboard pipeline, and script/story-structure sync surfaces.

## Next Steps

- Continue separating true dead code from intentional compatibility or side-effect imports.

## Linked Commits

- Pending.
