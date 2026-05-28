## User Prompt

Continue working toward the active goal: 让剧本达到商用水准.

## Goals

- Move script quality control from post-run audit into the provider chain itself.
- Prevent JSON-valid but commercially invalid DeepSeek scripts from triggering Timeline, image, video, and render work.
- Preserve live provider evidence for the new preflight behavior.

## Changes

- Added a provider-chain API regression where a terminal-failure cliffhanger returns valid JSON but must fail before media generation.
- Stored `structured_script_score` under `key_artifacts.script` immediately after script parsing.
- Made `generate_script()` raise `script_structured_quality_failed` when deterministic script structure checks fail.
- Classified `script_structured_quality_failed` as `script_quality_failed` in provider-chain failure categories.
- Added a cliffhanger regression for already executed delete commands, and rejected `命令已执行` / `已执行` as terminal-failure endings.
- Updated `commercial-script-quality.md` with Task 49-50.

## Validation

- Red test:
  - `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_api.py::test_generate_script_fails_before_media_when_structured_quality_fails -q`
  - Failed before implementation because `generate_script()` did not raise on a structured-quality failure.
- Green focused tests:
  - `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_api.py::test_generate_script_fails_before_media_when_structured_quality_fails tests/scripts/test_provider_chain_api.py::test_generate_script_disables_deepseek_streaming_and_thinking -q`
  - Passed: `2 passed, 26 warnings`.
  - `cd ai-pic-backend && pytest tests/scripts/test_production_cliffhanger_score.py::test_structured_score_rejects_executed_delete_command_as_cliffhanger -q`
  - Failed before adding `命令已执行` / `已执行` terminal phrases.
  - `cd ai-pic-backend && pytest tests/scripts/test_production_cliffhanger_score.py tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_failures.py -q`
  - Passed: `15 passed, 26 warnings`.
- Artifact recheck:
  - `artifacts/runs/quality-text-probe-dialogue-20260528Tlocal/text_probe.json` now fails structured scoring with `cliffhanger_unresolved_threat`.
  - `artifacts/runs/quality-text-probe-dialogue-v2-20260528Tlocal/text_probe.json` still passes structured scoring with `failed_checks=[]`.
- Live provider-chain smoke:
  - `python scripts/harness/provider_chain_regression.py --mode smoke --run-id quality-smoke-preflight-gate-20260528Tlocal --api-url http://localhost:8010 --episode-id 133 --script-id 117 --timeout-seconds 900 --poll-interval-seconds 5 --video-concurrency 1 --script-premise '数据中心日志被陌生操作者篡改，机器人必须拿到证据，结尾必须留下未知操作者或第二倒计时而不是失败完成'`
  - Passed with `ok=True`.
  - Evidence: `artifacts/runs/quality-smoke-preflight-gate-20260528Tlocal/provider_chain.json`.
  - The script artifact recorded `structured_script_score.passed=true`, `failed_checks=[]`, average `3.84`.
  - Timeline `63` rendered successfully; render probe output URL: `https://resource.lets-gpt.com/timeline-renders/video/20260528/123216/0857898c.mp4`.
- Audit note:
  - `python scripts/harness/production_quality_regression.py --mode audit-existing --run-id quality-audit-preflight-gate-20260528Tlocal --input-run artifacts/runs/quality-smoke-preflight-gate-20260528Tlocal/provider_chain.json`
  - Verdict remained `not_trial_ready` because audit-existing applies full-30s / visual consistency / sample-scale requirements to one smoke run, but it confirms structured script score passed.
- Final focused validation:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_cliffhanger_score.py tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_failures.py tests/scripts/test_production_quality_regression.py tests/scripts/test_provider_chain_payloads.py -q`
  - Passed: `35 passed, 27 warnings`.
  - `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_failures.py tests/scripts/test_provider_chain_api.py -q`
  - Passed after pre-commit formatting: `11 passed, 26 warnings`.
- Repository checks:
  - `python scripts/check_repo_docs.py`: `[check_repo_docs] ok`.
  - `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`: `[check_repo_contracts] ok (diff)`.
  - `git diff --check`: passed with no output.
  - `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files`: passed after `black` formatted `test_provider_chain_failures.py`; final rerun passed all enabled hooks, with `pytest (backend quick gate)` skipped because the focused pytest set covered this harness slice.

## Next Steps

- Run 10-sample or staged `live-10` evidence when provider cost/runtime is acceptable.
- Address the local audit-only `script_lint` false failure where cliffhanger LLM judgement is unavailable outside the API-backed lint path.

## Linked Commits

- Pending commit for this slice.
