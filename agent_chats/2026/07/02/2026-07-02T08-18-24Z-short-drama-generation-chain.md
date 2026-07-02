## User Prompt

PLEASE IMPLEMENT THIS PLAN: 短剧生成链路优化计划.

## Goals

- Keep the current `audio -> timeline -> clip -> render -> export` path as the single source of truth.
- Add short-drama production metadata, concept-test hints, quality scores, vertical visual contracts, localization/feedback placeholders, and a video-generation human review gate.
- Cover the behavior with backend and frontend tests.

## Changes

- Timeline import now adds short-drama root metadata: `production_context`, `concept_test_pack`, `short_drama_quality`, `localization_exports`, and `feedback_loop`.
- Timeline video clips now get `source_refs.vertical_visual_contract`, clip-level `short_drama_quality`, and pending `human_review` metadata.
- Provider-backed clip video rework now rejects review-gated clips unless `operator_reviewed` is true; the submitted task records that review flag.
- The frontend clip generation chain shows an operator review step, blocks video submit for pending review-gated clips, and sends `operator_reviewed` only after the operator confirms review.
- `docs/timeline-rendering-pipeline.md` documents the new optional Timeline Spec metadata.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/test_timeline_video_pause_policy.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_video_rework_review_gate.py -q` -> pass, 5 tests.
- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts` -> pass, 27 tests.
- `cd ai-pic-frontend && npm run lint` -> pass with 3 pre-existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ...` -> pass after splitting oversized helpers.
- `python scripts/check_repo_contracts.py --mode audit` -> pass.

2. Wider checks:

- `cd ai-pic-backend && python run_tests.py quick` -> failed before tests while installing dependencies. Pip reports `langchain-core==0.2.43` requires `pydantic>=2.7.4` on Python 3.13 while the repo pins `pydantic==2.5.0`.
- `cd ai-pic-frontend && npm run test` -> emitted passing output through the visible suites including the updated timeline clip rework controls, then did not exit for 90 seconds with no new output; interrupted with Ctrl-C, so not counted as a completed full-test pass.

3. Browser or MCP validation:

- Not run. No local app was listening on `localhost:8089`, `localhost:3000`, or `localhost:8000`, and the lite docker stack was not running.

## Next Steps

- Run the real browser Timeline clip flow once the local lite stack is up.
- Resolve the Python 3.13 dependency conflict or run backend quick in the repo-supported Python version.

## Linked Commits

- Pending.
