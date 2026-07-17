## User Prompt

The Timeline management surface cannot generate video because it has no visible model selector and no visible human-review entry.

## Goals

- Keep video model selection visible in the primary clip-video action surface.
- Keep the required human-review checkbox visible so operators can clear the generation gate.
- Preserve the existing collapsed area for lower-frequency motion, resolution, ratio, reason, binding, and reference controls.
- Verify the current Timeline 76 clip flow without starting a billable Provider task.

## Changes

- Moved the existing video model selector and read-only Timeline target duration out of the compact parameter popover.
- Moved the required human-review checkbox out of the collapsed reference section.
- Extracted the review row into the existing card-sections module to keep the main card under the repository file-size limit.
- Added regression assertions that both controls remain outside collapsed `details` elements and that review still enables video submission.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npm run lint` -> passed with 0 errors and 3 existing warnings.
- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts tests/timelineWorkspaceLayout.test.tsx` -> 69 passed.
- `cd ai-pic-frontend && npm run test` -> 433 passed, 9 failed in the unrelated dirty Canvas WIP (`ProductionCanvasChatBar` and `ProductionCanvasPlanner`); no Timeline test failed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed after extracting the review row; the main card is 245 lines.
- `pre-commit run --files <this scoped change>` -> passed.
- `git diff --check` -> passed.
- `npm run build` was not required because no route, layout, config, auth, server/client boundary, or hydration behavior changed.
- `pre-commit run --all-files` was not repeated because the same work session already established unrelated repository-wide baselines: 68 existing Ruff findings, historical ledger-format failures, and one `story_parser` failure. The exact four-file change is covered by the scoped run above.
- `./docker/build_prod_images.sh` was not repeated because the same work session already reached the external Docker Hub metadata step and was blocked fetching `python:3.11-slim`, before this frontend code could compile.

2. Browser validation:

- Entry URL: `http://localhost:8090/episodes/a48f8d1010044807baf22e113e1f89c1/workspace?tab=timeline&scriptId=146&clipId=video_scene_591_beat_4352_001`.
- Before: the video model select had 13 Provider models but was inside a closed parameter popover; the human-review checkbox was inside a separate closed reference section, leaving only a disabled generation button visible.
- After: the model select and review checkbox are visible in step 3. Selecting `volcengine:doubao-seedance-2-0-260128` and checking review enables `生成/重做此片段视频`.
- Network: `GET /api/v1/ai/models/available?model_type=video` returned 200.
- Console: no new errors. The only observed 404 remains the pre-existing missing environment image `/uploads/1321c06378624d909b07f8e4c3d5ef7a.png`.
- Preferred Chrome DevTools transport timed out; the repository harness rerun passed with its recorded Playwright fallback. Interactive verification also passed in the Codex in-app browser.
- Evidence: `artifacts/runs/timeline-video-controls-20260717T103002Z/`.

3. Conflict signals and corrections:

- Initial symptom: the page appeared to have no video-model capability.
- Contradicting evidence: the hidden select already contained 13 Provider models and the model endpoint returned 200.
- Correction: treat this as a discoverability/gating defect, not an API or Provider defect, and expose the two required controls without duplicating state.
- One browser interaction call timed out while returning its result, but a fresh DOM snapshot showed the selection and review state had applied; the final direct state check and screenshot confirmed the enabled button.

## Next Steps

- None for this fix. A real Provider task was intentionally not submitted because the UI path was fully proven without incurring generation cost.

## Linked Commits

- This commit.
