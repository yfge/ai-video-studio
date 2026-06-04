## User Prompt

PLEASE IMPLEMENT THIS PLAN: Episode 153 Script Generation Recovery Plan. Fix DeepSeek v4-pro beat-contract JSON truncation for task 6005, keep explicit v4-pro semantics, rerun script generation for episode 153, verify a `script:<id>` result in the operator UI, add tests, ledger, and commit only the backend fix/tests/ledger.

## Goals

- Disable DeepSeek v4-pro reasoning for strict JSON repair/generation paths where reasoning tokens were consuming output budget.
- Preserve explicit `deepseek:deepseek-v4-pro` provider/model behavior without silently falling back.
- Keep raw provider bodies out of task errors while adding concise token/provider diagnostics.
- Keep script quality gates intact.
- Rerun episode 153 and record honest runtime evidence.

## Changes

- Added `app/services/providers/deepseek_strict_json.py` with shared DeepSeek v4-pro strict JSON kwargs: `thinking={"type": "disabled"}`.
- Updated `app/services/script/beat_contract_generation.py` so beat-contract generation and repair pass the strict JSON kwargs for explicit DeepSeek v4-pro calls.
- Changed beat-contract repair to use `_BEAT_CONTRACT_MAX_TOKENS` instead of the smaller generic repair budget.
- Added structured invalid JSON diagnostics: provider, model, finish_reason, max_tokens, completion_tokens, reasoning_tokens.
- Added `app/services/script/beat_contract_canonicalizer.py` and wired it into `beat_contract_normalizer.py` to canonicalize finite provider beat/scene enum aliases seen in live DeepSeek outputs (`escalation`, `confirmation`, `action`, `conflict_escalation`, etc.) while preserving validation failure for unknown values.
- Updated generic quality-gate repair to pass the same DeepSeek v4-pro strict JSON kwargs; this was needed after live task 6011 reached quality repair and waited on a DeepSeek strict JSON repair call.
- Added focused unit tests for DeepSeek v4-pro thinking disable, diagnostics, repair token budget, alias canonicalization, unknown enum preservation, and generic quality-gate repair behavior.

## Validation

- RED first:
  - `docker exec -i ai-video-backend pytest tests/unit/services/script/test_beat_contract_generation.py tests/unit/services/ai/test_scripts_ai_manager_failures.py -v`
  - Failed before implementation because DeepSeek v4-pro beat-contract calls lacked `thinking={"type":"disabled"}` and invalid JSON errors lacked diagnostics.
- Target tests:
  - `docker exec -i ai-video-backend pytest tests/unit/services/script/test_beat_contract_canonicalizer.py tests/unit/services/script/test_beat_contract_normalizer.py tests/unit/services/test_quality_gate_repair.py tests/unit/services/script/test_beat_contract_generation.py tests/unit/services/ai/test_scripts_ai_manager.py tests/unit/services/ai/test_scripts_ai_manager_failures.py -q`
  - Result: 15 passed.
- Repo docs:
  - `python scripts/check_repo_docs.py`
  - Result: ok.
- Repo contracts:
  - `python scripts/check_repo_contracts.py --mode diff <changed backend/test files>`
  - Result: ok.
- Limited pre-commit:
  - `pre-commit run --files <episode 153 script-generation files>`
  - Static hooks, repository docs/contracts, and ledger enforcement passed. The backend quick gate reported `1927 passed, 59 skipped`, but the hook exited non-zero with `files were modified by this hook` in the already dirty worktree; no unrelated files were staged.
  - `pre-commit run --all-files` was not run because the worktree contains many unrelated timeline/storyboard/frontend changes outside this task.
- Backend quick baseline:
  - `docker exec -i ai-video-backend python run_tests.py quick`
  - Result: failed during collection with existing `tests/scripts/*` import/collection errors; not caused by the touched files. Target tests above passed.
- Production image build:
  - `./docker/build_prod_images.sh` was not run for this scoped backend fix; this remains a release-time validation gap.
- Runtime attempts:
  - Restarted `ai-video-backend` and `ai-video-celery-worker`.
  - API task 6007: original JSON truncation was gone; failed on provider enum drift (`escalation`, `reaction`, `discovery`, etc.).
  - API task 6008: failed on additional enum drift (`confirmation`).
  - API task 6009: failed on legacy enum drift (`action`) and `conflict_escalation`.
  - API tasks 6010/6011/6014: progressed beyond beat-contract invalid JSON/enum failures, but long live generation was interrupted by dev container restarts, leaving rows in `processing`.
  - One-off direct processor tasks 6016/6018: avoided the常驻 worker restart issue, but live DeepSeek direct generation calls did not return within the wait window and were stopped; rows remain `processing`.
  - DB evidence after attempts: `scripts_for_episode_153 []`; no `script:<id>` was created.
- Browser evidence:
  - Chrome DevTools failed to connect: `http://127.0.0.1:9222/json/version` returned HTTP Not Found.
  - Playwright fallback with system Chrome logged in and opened `http://localhost:8089/episodes/153/workspace`.
  - Screenshot: `artifacts/runs/episode-153-script-recovery-20260604/operator-ui-auth.png`.
  - UI text showed episode 153 workspace still has `暂无剧本`.

## Next Steps

- The durable `beat_contract_invalid_json` root cause is fixed in code and covered by tests.
- Live episode 153 rerun still needs a stable provider/runtime window to complete script persistence. Current blockers were live DeepSeek direct-generation hangs and dev container restarts during long tasks, not the original truncated beat-contract JSON.
- Clean up or explicitly resolve stale processing task rows from validation attempts if they should not remain visible in operator task lists.
- Consider adding request-level timeouts/diagnostics for long DeepSeek direct generation and generic quality repair calls so future runs fail precisely instead of leaving tasks in `processing`.

## Linked Commits

- This commit.
