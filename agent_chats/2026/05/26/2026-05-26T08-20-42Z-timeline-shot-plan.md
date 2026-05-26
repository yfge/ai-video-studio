## User Prompt

PLEASE IMPLEMENT THIS PLAN: Timeline-First 全链路补齐计划。

## Goals

- Add a real Timeline-native shot-plan step before media generation.
- Keep Timeline Spec v1 as the system of record; do not add a new DB table.
- Preserve stable clip ids and timing while writing shot-plan metadata onto video clips.

## Changes

- Added `TimelineShotPlanRequest` with provider/model/style/version-lock fields.
- Added `POST /api/v1/timelines/{timeline_id}/shot-plan`.
- Added `TimelineShotPlanService`, which reads Timeline clips, calls the configured text model for structured JSON, validates one shot per video clip, and writes `source_refs.timeline_shot_plan` back to Timeline Spec with a new version.
- Added API regression coverage for stable clip identity, provider/model lineage, revision creation, and invalid-plan no-write behavior.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_shot_plan_api.py -q` passed: `2 passed`.
- `git diff --check -- ai-pic-backend/app/schemas/timeline.py ai-pic-backend/app/services/timeline_shot_plan_service.py ai-pic-backend/app/api/v1/endpoints/timelines.py ai-pic-backend/tests/test_timeline_shot_plan_api.py` passed for tracked files before staging.
- Browser/Chrome validation was not run for this commit; this commit adds a backend API and deterministic API tests. The live provider-chain validation is reserved for the final harness commit after the whole Timeline-first path is wired.

## Next Steps

- Wire the product timeline pipeline and production placeholder path to generate shot plans before storyboard support and image queueing.
- Update provider-chain harness to require shot-plan prompts from Timeline readback before any Seedance call.

## Linked Commits

Pending
