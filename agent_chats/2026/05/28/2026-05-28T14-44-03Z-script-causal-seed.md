## User Prompt

commit

## Goals

- Improve first-pass commercial script quality without weakening the text-only 10-sample gate.
- Seed later passwords, accounts, tokens, remote cursors, supplier callbacks, and hidden markers with visible causal metadata.
- Preserve the active goal status: do not claim commercial quality until the live gate proves it.

## Changes

- Added `causal_seed` to the provider-chain script JSON prompt and schema.
- Rendered scene `causal_seed` into the screenplay text sent to ScriptScore.
- Required the prompt to name owner, access rule, limitation, and motive for causal seeds that support later plot devices.
- Expanded structured opening-hook markers so reused or identical reference images and hidden markers count as visible opening anomalies.
- Added red/green tests for schema inclusion, prompt contract alignment, screenplay rendering, and the reference-image reuse hook case.

## Validation

- Red/green targeted tests:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_hook_score.py::test_structured_score_accepts_reference_reuse_as_visual_anomaly_hook tests/scripts/test_provider_chain_script_prompt.py::test_build_script_prompt_aligns_with_script_score_pass_rubric tests/scripts/test_provider_chain_script_prompt.py::test_provider_chain_script_text_preserves_causal_seed_metadata tests/scripts/test_provider_chain_api.py::test_generate_script_disables_deepseek_streaming_and_thinking -q`
  - Failed before implementation with missing hook marker, missing prompt/schema `causal_seed`, and missing rendered causal metadata.
  - Passed after implementation: `4 passed, 26 warnings`.
- Focused regression set:
  - `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_script_prompt.py tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_payloads.py tests/scripts/test_production_hook_score.py tests/scripts/test_production_quality_regression.py tests/scripts/test_production_script_quality_regression.py -q`
  - Passed: `42 passed, 27 warnings`.
- Live text probe against `http://localhost:8010`:
  - `python scripts/harness/production_script_quality_regression.py --run-id script-quality-live-text-10-causal-seed-hook-20260528Tlocal --api-url http://localhost:8010 --sample-count 10 --timeout-seconds 900`
  - Verdict: `script_quality_not_proven`.
  - First-pass success improved to 7/10 from the previous best 6/10.
  - Retry-adjusted success stayed at 9/10.
  - Script score average: 4.03; lint average: 9.85; structured average: 3.81; provider billing/quota errors: 0.

## Next Steps

- Continue targeting first-attempt quality. Current remaining failures are concentrated in token/permission causality, unknown-operator motivation, character recognizability, and generic dramatic-purpose wording.
- Do not mark the overall commercial-script-quality goal complete until a live 10-sample run reaches at least 8/10 first-pass and keeps retry-adjusted quality stable.

## Linked Commits

- Pending commit for this slice.
