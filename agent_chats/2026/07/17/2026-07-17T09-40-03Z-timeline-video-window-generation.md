## User Prompt

Implement the Timeline video-shot generation optimization: aggregate audio beats into scene-local 5-8 second video windows targeting 6 seconds, keep dialogue/subtitle timing exact, adapt Provider durations, protect produced legacy Timelines, and verify Timeline 76 end to end.

## Goals

- Make `beat_window_v2` the shared Timeline video segmentation strategy without changing `timeline.v1` or adding a migration.
- Preserve audio/subtitle clips while generating continuous scene-local video windows and stable legacy aliases.
- Rebuild shot-plan context from every overlapping event in a grouped window.
- Treat Timeline duration as the generation SSOT and audit Provider duration adaptation on every attempt.
- Upgrade only safe legacy Timelines and validate the real Timeline 76 data path.

## Changes

- Replaced short-pause-only handling with deterministic scene window partitioning using 5s minimum, 6s target, 8s maximum, and a 3s tail minimum.
- Added grouped beat lineage, source clip aliases, stable `_part_N` long-beat IDs, segmentation metadata, and overlap-based shot-plan prompts.
- Added automatic-upgrade protection for generated video assets, active video tasks, and render history.
- Added Provider/model duration resolution per fallback attempt plus target/provider/allowed-duration/capability audit fields in successful and failed generation records.
- Kept the deprecated request `duration` field for compatibility while ignoring it as a Timeline target override.
- Upgraded Timeline 76 from v3 to v4, then generated 10 fresh DeepSeek shot plans in v5.

## Validation

- `AI_FORCE_MOCK=true pytest -q <Timeline/import/shot-plan/provider-duration targets>`: 72 passed.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed.
- `pre-commit run --files <changed files>`: passed, including the backend quick gate and frontend lint.
- `pre-commit run --all-files` in an isolated clean worktree: blocked by repository baseline (68 pre-existing Ruff findings, historical ledger files rewritten by formatting hooks, and `test_extract_json_block_reexported_from_story_parser`; backend quick result 1 failed, 2249 passed, 61 skipped). No repository-wide formatting was copied back.
- Clean-worktree full backend run with `AI_FORCE_MOCK=true`: 2 failed, 2649 passed, 96 skipped. The failures are the pre-existing Canvas single-video `virtual_ip_id=None` case and a mock-mode script dialogue fallback case; no Timeline test failed.
- Exact `python run_tests.py quick` setup was blocked by the current Python 3.13 environment dependency conflict (`pydantic==2.5` versus `langchain-core==0.2.43` requiring `pydantic>=2.7.4`); the repository pre-commit backend quick gate itself ran.
- `./docker/build_prod_images.sh` was attempted in a clean isolated worktree. Both the multi-arch build and its amd64 retry stalled while loading Docker Hub metadata for `python:3.11-slim`; the build was canceled before code compilation and no image was pushed.
- Timeline 76 live preflight: 60s, 36 video clips, 18 dialogue clips, 18 subtitle clips, no video assets, no active video tasks, and no render jobs.
- Timeline 76 live v5: 10 video clips, 18 dialogue clips, 18 subtitle clips, durations `[6390, 6037, 5573, 5431, 5405, 6164, 6639, 7361, 8000, 3000]` ms, and 10/10 shot plans.
- Real Provider acceptance: task 6452 succeeded with `volcengine:doubao-seedance-2-0-260128`; target 6.39s, Provider request 8s, allowed `[4, 6, 8]`, capability source `volcengine`. The persisted output is 153 frames at 24fps (6.375s), a 15ms difference below one frame (41.667ms).
- Browser evidence: `artifacts/runs/timeline-window-v2-20260717T174300/` (Chrome transport failed; the recorded Playwright fallback passed). The only observed 404 was the pre-existing missing environment image `/uploads/1321c06378624d909b07f8e4c3d5ef7a.png`.

## Next Steps

- None for the requested fixed policy. Add configurable rhythm presets only if real sample review shows the fixed 5/6/8 second policy is insufficient.

## Linked Commits

- This backend commit.
