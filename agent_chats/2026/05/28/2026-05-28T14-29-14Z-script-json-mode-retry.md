## User Prompt

Continue working toward the active goal: 让剧本达到商用水准.

## Goals

- Remove malformed script JSON as a blocker in the text-only commercial script gate.
- Make structured script failures feed concrete repair notes into retries.
- Preserve the full success bar: do not claim commercial quality until the 10-sample evidence proves it.

## Changes

- Added `json_schema` passthrough to `/api/v1/ai/generate/text`.
- Mapped DeepSeek schema requests to JSON mode via `response_format={"type":"json_object"}`.
- Extracted the provider-chain script request body and schema into `provider_chain_script_request.py`.
- Sent provider-chain script generation through schema-backed JSON mode with non-streaming DeepSeek v4 flash, thinking disabled, `max_tokens=2600`, and `temperature=0.2`.
- Preserved structured script gate failures in text-only regression samples so retry repair notes include failed checks such as `opening_hook_substance` and `dialogue_line_length`.
- Tested and rejected two prompt experiments that worsened live 10-sample evidence; those prompt changes were reverted and are not part of this slice.

## Validation

- Red/green tests:
  - `cd ai-pic-backend && pytest tests/unit/test_ai_text_generation_route.py tests/unit/test_deepseek_provider_v4.py::test_build_chat_request_maps_json_schema_to_json_object_response_format tests/scripts/test_provider_chain_api.py::test_generate_script_disables_deepseek_streaming_and_thinking -q`
  - Failed first with missing route schema, missing DeepSeek JSON mode mapping, and missing harness `json_schema`; passed after implementation.
  - `cd ai-pic-backend && pytest tests/scripts/test_production_script_quality_regression.py::test_failed_sample_preserves_structured_score_for_repair_notes tests/scripts/test_production_script_quality_regression.py::test_repair_notes_include_script_score_and_structured_feedback -q`
  - Failed first because `_failed_sample` dropped structured score payload; passed after preserving the structured failure.
- Focused regression set:
  - `cd ai-pic-backend && pytest tests/unit/test_ai_text_generation_route.py tests/unit/test_deepseek_provider_v4.py tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_payloads.py tests/scripts/test_production_script_quality_regression.py tests/scripts/test_provider_chain_script_prompt.py tests/scripts/test_production_quality_regression.py -q`
  - Passed: `45 passed, 31 warnings`.
- Live text probes against `http://localhost:8010`:
  - `script-quality-live-text-3-json-mode-20260528Tlocal`: 3/3 first-pass successes, script score average 4.10, no JSON parse failures.
  - `script-quality-live-text-10-json-mode-20260528Tlocal`: verdict `script_quality_not_proven`, first-pass 5/10, retry-adjusted 8/10, script score average 4.08.
  - `script-quality-live-text-10-json-mode-temp02-20260528Tlocal`: verdict `script_quality_not_proven`, first-pass 5/10, retry-adjusted 8/10, script score average 4.11.
  - `script-quality-live-text-10-json-mode-structured-feedback-20260528Tlocal`: verdict `script_quality_not_proven`, first-pass 6/10, retry-adjusted 9/10, script score average 4.09, lint average 9.85, structured average 3.83, provider billing/quota errors 0.

## Next Steps

- The goal is still active. The current best 10-sample evidence satisfies retry-adjusted stability but misses the first-pass requirement: 6/10 versus the required 8/10.
- Next work should target first-attempt quality: recurring logic gaps around permissions/accounts, weak character motivation, and opening-hook substance on quieter premises.

## Linked Commits

- Pending commit for this slice.
