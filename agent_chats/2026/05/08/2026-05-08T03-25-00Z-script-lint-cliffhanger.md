## User Prompt

最近的任务失败

check_cliffhanger 使用 prompt 进行检查，不要用这种硬编码

## Goals

- Replace hardcoded cliffhanger marker matching with prompt-based LLM judgement.
- Keep deterministic script lint checks unchanged for scene headers, pacing, hook, dialogue length, and visual language.
- Route generation quality gates through the async lint path so failed cliffhanger judgement triggers the existing repair loop.
- Keep standalone quality checks as review-only paths that persist or return failed lint results when judgement fails.

## Changes

- Added a prompt-based async cliffhanger checker using `ai_manager.generate_text(...)` and strict JSON fields: `passed`, `score`, `reason`, `evidence`, and `suggestion`.
- Moved the cliffhanger judgement prompt into PromptManager templates as `script_cliffhanger_judgement` and reused the existing strict JSON system prompt template.
- Added `lint_script_content_async(...)` and kept the synchronous lint entrypoint as compatibility-only; without an LLM it fails the cliffhanger rule with `cliffhanger_llm_unavailable`.
- Passed `model` and `prefer_provider` from script generation quality-gate repair into async lint, so failed cliffhanger judgement blocks generation and triggers repair.
- Updated the standalone quality API and Celery review task to call the async lint path with the default text model path when no generation model metadata exists.
- Replaced cliffhanger keyword assertions with mocked LLM judgement tests, including pass, fail, unavailable, generation repair, endpoint, and task coverage.
- Moved task DB lookups behind repositories to keep the touched Celery entrypoint aligned with repository contracts.

## Validation

- `cd ai-pic-backend && pytest tests/test_script_quality_lint.py tests/unit/services/test_narrative_quality_gate.py tests/unit/services/test_script_cliffhanger_quality_gate.py -v`
  - Result: 17 passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Result: passed.
- Follow-up correction after confirming prompt management:
  - Added PromptManager template files for `script_cliffhanger_judgement`.
  - Re-ran pytest target set: 17 passed.
  - Re-ran diff contract: passed.

## Next Steps

- Consider re-running the failed production script generation path after backend/worker reload if runtime confirmation is needed.

## Linked Commits

- None
