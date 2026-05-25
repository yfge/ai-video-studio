# Main Chain Commercial Readiness

## Current State

The product direction remains a professional short-drama production system, not
a consumer APP, generic SaaS, or social creation feed. Timeline is still the
single source of truth for playable output, and the near-term goal is to make one
narrow production chain reliable enough to carry real content work.

Implemented baseline:

- Timeline Spec v1, timeline/render/media tables, version locking, and render
  job idempotency exist.
- `audio_timeline.beats` can be imported into Timeline Spec v1 and consumed by
  storyboard support generation.
- Timeline render/export worker, `media_assets` output persistence, operator
  render panel, and the render/export harness path are packaged in git.

Open constraint:

- Phase 1 is complete. The previous dirty worktree was split into four atomic
  commits: `95857e9b`, `8251d67f`, `657b3a35`, and `7bade488`.
- Real `Episode -> Timeline -> Render -> Export` evidence has reached the render
  job boundary, but has not passed because Timeline video clips do not yet
  resolve to legacy storyboard/video task assets.

## Phase 1: Close Current Worktree

Tasks:

- [x] Split the current worktree into reviewable boundaries: Timeline render/export,
      Codex/ChatGPT provider plus `chatgpt-img-2`, and IP content fill with
      DeepSeek.
- [x] Keep unrelated runtime code untouched while staging each boundary.
- [x] Ensure every code boundary has its matching `agent_chats` ledger entry.

Exit criteria:

- [x] Each boundary has focused validation recorded in its ledger.
- [x] No broad feature work starts before this worktree is packaged.

## Phase 2: Prove Real Render/Export

Tasks:

- Choose or create one script whose Timeline video clips resolve to actual video
  assets or storyboard frame videos.
- Run the real `Episode -> Timeline -> Render -> Export` path through the
  operator flow or golden-path harness.
- Store evidence under `artifacts/runs/<run_id>/`, including the actual browser
  engine or fallback.

Exit criteria:

- A render job reaches `succeeded`.
- `render_jobs.output_asset` exposes a usable `file_url` or `file_path`.
- The evidence proves the route used a locked Timeline version.

Latest attempt:

- `python scripts/harness/run_golden_path.py --scenario timeline_export_end_to_end --run-id main-chain-e2e-20260525T031832Z --api-url http://localhost:8000 --base-url http://localhost:8089 --username geyunfei --password '<redacted>' --script-id 122 --timeout-seconds 300`
- Evidence: `artifacts/runs/main-chain-e2e-20260525T031832Z/golden_path.json`.
- Result: failed after reaching `POST /api/v1/timelines/1/render`.
- Render job `1` consumed locked Timeline `1` version `1`, then failed with
  `missing_video_url` for 30 video clips and no `output_asset`.
- The same run shows task `5986` ended failed with
  `storyboard_has_assets_refuse_overwrite: set overwrite_existing=true`.
- Database check showed existing succeeded `video_generation_tasks` for script
  `122`, but current storyboard frames do not carry `timeline_clip_id`, and no
  `media_assets` rows exist. This makes Phase 5 clip asset lineage a prerequisite
  for a clean Phase 2 pass unless a better fixture script is created.

## Phase 3: Add Timeline Delete And Rollback

Tasks:

- Add safe delete/restore semantics for timelines and render attempts using the
  existing soft-delete pattern.
- Add rollback to a prior timeline version without mutating the old render
  outputs.
- Surface rollback state clearly in Timeline API responses.

Exit criteria:

- API tests cover delete, restore, rollback, permission checks, and stale version
  conflicts.
- Existing render jobs remain traceable after rollback.

## Phase 4: Harden Timeline Spec Validation

Tasks:

- Add schema validation for Timeline Spec v1 envelope, tracks, clips, source
  fields, timing, and asset references.
- Validate imports from `audio_timeline.beats` before persistence.
- Make invalid specs fail with actionable errors instead of later render-time
  failures.

Exit criteria:

- Tests reject malformed tracks, missing `clip_id`, non-monotonic timing, and
  invalid source references.
- Import tests prove dialogue/video/subtitle clips preserve stable identity and
  provenance.

## Phase 5: Finish Clip Asset Lineage And Rework Actions

Tasks:

- Treat start frames, end frames, storyboard images, storyboard videos, and final
  clip videos as first-class clip assets.
- Link assets to stable `clip_id` values rather than temporary frame indexes.
- Implement re-dub, re-cut, and re-render around stable clip identity.

Exit criteria:

- Re-dub/re-cut/re-render do not change the original `clip_id`.
- Operator UI can show source audio, source frame, generated video, output asset,
  and replacement history for a selected clip.

## Phase 6: Produce Ten Narrow Samples

Tasks:

- Pick one narrow vertical and 2-3 reusable characters.
- Produce 10 vertical samples, each 30-60 seconds.
- Record cost, generation time, failure points, manual fixes, selected models,
  output file, and reusable prompt/workflow decisions.

Exit criteria:

- At least 10 exported samples exist with production metrics.
- The team can identify which parts of the workflow are repeatable and which
  still require manual intervention.
- Follow-up tasks are based on production evidence, not platform expansion.
