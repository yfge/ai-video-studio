## User Prompt

PLEASE IMPLEMENT THIS PLAN: Timeline-First 全链路补齐计划。

## Goals

- Make the product timeline pipeline generate Timeline-native shot plans before storyboard/image work.
- Make storyboard support frames prefer `source_refs.timeline_shot_plan` instead of only reverse-building frames from dialogue beats.
- Keep file-size contracts clean after adding shot-plan logic.

## Changes

- Added a worker-friendly `generate_shot_plan_for_timeline` path on `TimelineShotPlanService`.
- Wired `timeline_pipeline.py` and `production_storyboard.py` to generate shot plans immediately after Timeline Spec import.
- Added `storyboard_from_timeline_shot_plan.py` and `timeline_shot_plan_payloads.py` to keep service files below contract limits.
- Updated Timeline storyboard support generation to prefer video clip shot plans and persist `generation_method=timeline_shot_plan`.
- Updated pipeline and storyboard tests to prove shot-plan generation happens before storyboard support and that storyboard frames carry Timeline shot-plan lineage.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_shot_plan_api.py tests/unit/services/audio/test_storyboard_from_timeline_spec.py tests/integration/test_timeline_pipeline_import_api.py -q` passed: `7 passed`.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed after splitting oversized files.
- `git diff --check` passed.
- Browser/Chrome validation was not run for this commit; no frontend route was changed. Live system API/browser validation is reserved for the final provider-chain harness commit.

## Next Steps

- Tighten the provider-chain harness so Seedance video generation can only read Timeline shot-plan prompts from Timeline readback.
- Persist per-run Timeline spec snapshots and clip asset readback evidence.

## Linked Commits

Pending
