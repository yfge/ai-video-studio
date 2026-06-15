---
id: story-episode-production-prompt-2026-06-15
date: 2026-06-15
participants:
  - user
  - codex
models:
  - GPT-5
tags:
  - ai-pic-backend
  - story-generation
  - episode-generation
  - production-quality
  - prompt-engineering
related_paths:
  - ai-pic-backend/app/prompts/templates/story_outline_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_step_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline_short_drama.txt
  - ai-pic-backend/app/services/story_quality_gate.py
  - ai-pic-backend/app/services/episode_contract_quality.py
  - ai-pic-backend/app/services/narrative_quality_gate.py
  - ai-pic-backend/app/api/v1/endpoints/stories/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
summary: Production async story and episode prompt, contract, and quality-gate upgrade after research.
---

## User Prompt

The user requested implementation of the "Story/Episode Prompt Upgrade After Research" plan. The plan applies the same production-quality approach previously used for script generation to async story and episode generation, based on the following research references:

- Filmustage vertical drama guide: https://filmustage.com/blog/how-to-write-a-vertical-drama-script/
- Hongguo short-drama writing lessons 05, 06, 08, and 09:
  - https://www.juben.pro/a/1-1783.html
  - https://www.juben.pro/a/1-1784.html
  - https://www.juben.pro/a/1-1787.html
  - https://www.juben.pro/a/1-1788.html
- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Evaluation-driven prompt iteration: https://arxiv.org/html/2601.22025v1

## Goals

- Upgrade production-only async story and episode prompts into structured production briefs instead of simple rule lists.
- Force `/stories/generate-async` and `/episodes/generate-async` payloads into `generation_mode="production"` while keeping sync generation defaulted to `standard`.
- Propagate `generation_mode`, `production_mode`, prompt version, and contract version through LangGraph and direct fallback paths.
- Block production legacy prose, logline-only, abstract, or missing-contract outputs before persistence.
- Write quality-gate failure details into task metadata without adding a database migration.
- Preserve standard/sync behavior.

## Changes

- Reworked `story_outline_short_drama` with a production story-room brief and `structured_story_contract` covering target audience, core emotional pain, big expectation, small-expectation ladder, protagonist goal, structural conflict, information gap, first-three-episode spine, stage highs, shootability, compliance risks, and traffic hooks.
- Reworked `episode_step_outline`, `episode_generation_short_drama`, and `episode_from_outline_short_drama` with production requirements for 0-3 second ignition, first-30-second retention reason, midpoint conflict/information movement, payoff, natural final button, dialogue function tags, close-up visual anchors, action, obstacle, cost, choice, and information delta.
- Added production mode to async story and episode request payloads and propagated it through story/episode generation services, LangGraph agents, outline generation, direct fallback generation, and agent-run metadata.
- Added `story_quality_gate.py` and `episode_contract_quality.py`, exported story gate evaluation through `narrative_quality_gate.py`, and extended episode quality-gate enforcement with `require_episode_contract`.
- Production story generation now blocks missing or weak `structured_story_contract` output before creating a story; production episode generation now blocks missing or weak `structured_episode_contract` output and does not preserve low-quality production episodes.
- Production direct fallback paths now use the production prompt variables and skip legacy/mock fallback output.
- Refactored touched backend files to keep repository contracts clean: extracted script scoring schemas, episode direct generation helpers, episode generation context helpers, and repository access for virtual IP lookups.
- Preserved backward-compatible `app.schemas.generation` exports for script scoring models after extracting them to `script_scoring.py`.
- Split the larger mock script payload into `mock_ai_script_payloads.py` to keep test fixture files within repository size contracts.
- Updated mock AI fixtures so generated story, episode, and script payloads satisfy the stronger structured contracts used by tests.
- Added and updated unit/integration tests for production prompt content, async production payload propagation, direct fallback prompt usage, contract gates, and production logline-only rejection.

## Validation

- Passed:
  - `cd ai-pic-backend && pytest tests/unit/services/test_story_agent_quality_gate.py tests/unit/services/story/test_story_outline_quality.py tests/unit/services/ai/test_episode_generation_strict.py tests/unit/services/test_narrative_quality_gate.py tests/unit/test_episode_async_incremental_persistence.py tests/integration/test_task_pipeline_agent_run_audit.py -q`
  - Result: 16 passed.
- Passed:
  - `cd ai-pic-backend && pytest tests/unit/services/test_story_agent_quality_gate.py tests/unit/services/story/test_story_outline_quality.py tests/unit/services/ai/test_episode_generation_strict.py tests/unit/services/test_narrative_quality_gate.py tests/unit/test_episode_async_incremental_persistence.py tests/integration/test_task_pipeline_agent_run_audit.py tests/unit/test_production_story_episode_prompt_templates.py tests/unit/services/test_episode_contract_quality_gate.py tests/unit/services/story/test_story_production_quality_gate.py tests/unit/services/ai/test_story_outline_generation_mixin.py tests/unit/test_episode_step_outline_light.py -q`
  - Result: 29 passed, 92 warnings.
- Passed after the script-scoring compatibility export fix:
  - `cd ai-pic-backend && pytest tests/unit/services/scoring/test_script_score_service.py tests/unit/services/scoring/test_traffic_sheet_service.py tests/unit/services/test_story_agent_quality_gate.py tests/unit/services/story/test_story_outline_quality.py tests/unit/services/ai/test_episode_generation_strict.py tests/unit/services/test_narrative_quality_gate.py tests/unit/test_episode_async_incremental_persistence.py tests/integration/test_task_pipeline_agent_run_audit.py tests/unit/test_production_story_episode_prompt_templates.py tests/unit/services/test_episode_contract_quality_gate.py tests/unit/services/story/test_story_production_quality_gate.py tests/unit/services/ai/test_story_outline_generation_mixin.py tests/unit/test_episode_step_outline_light.py -q`
  - Result: 50 passed, 102 warnings.
- Passed:
  - `python scripts/check_repo_docs.py`
  - Result: `[check_repo_docs] ok`.
- Passed:
  - `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Result: `[check_repo_contracts] ok (diff)`.
- Passed:
  - `git diff --check`
  - Result: no whitespace errors.
- Passed:
  - `pre-commit run ruff --files <changed files>`
  - `pre-commit run black --files <changed files>`
  - `pre-commit run isort --files <changed files>`
  - Result: all clean after hook formatting was applied.
- Passed:
  - Prompt render smoke with `PromptManager` for production story and episode templates.
  - Result: `render-ok`.
- Blocked:
  - `cd ai-pic-backend && python run_tests.py quick`
  - Result: setup failed before tests because the Python 3.13 dependency resolver found an incompatible pin: `pydantic==2.5.0` conflicts with `langchain-core==0.2.43`, which requires `pydantic>=2.7.4` on Python `>=3.12.4`.
- Failed before commit:
  - `pre-commit run --all-files`
  - Result: repository-wide hooks touched unrelated historical EOF files and reported existing all-repo ruff issues outside this change. The run also exposed a missing `ScriptScoreResult` compatibility export, which was fixed here. Hook-made unrelated file edits were restored before staging.
- Failed before commit:
  - `pre-commit run --files <changed files>`
  - Result: file-level format/doc/contract/ledger hooks passed after formatting, but the `backend-pytest` hook still collected the broader backend suite and failed on existing script harness export errors outside this story/episode change: `_BEAT_CONTRACT_MAX_TOKENS`, `structured_script_score`, and `STRUCTURED_SCORE_PASS`.

## Next Steps

- Resolve the backend quick-suite dependency conflict for Python 3.13, then rerun `cd ai-pic-backend && python run_tests.py quick`.
- Run provider-backed browser validation for `/stories/generate-async` and `/episodes/generate-async` when the local runtime and credentials are available.
- Monitor production failure rate after rollout because stricter contracts can intentionally reject weak generations before persistence.

## Linked Commits

- This change is intended to be committed as one Conventional Commit with the implementation, tests, and this ledger entry.
