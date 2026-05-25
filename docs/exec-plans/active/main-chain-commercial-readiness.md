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
  render panel, and the render/export harness path exist in the current worktree.

Open constraint:

- Current changes are still uncommitted and span multiple concerns. They must be
  split or reviewed before more feature work is added.
- Real `Episode -> Timeline -> Render -> Export` evidence is still required with
  a script that already has renderable video clips.

## Phase 1: Close Current Worktree

Tasks:

- Split the current worktree into reviewable boundaries: Timeline render/export,
  Codex/ChatGPT provider plus `chatgpt-img-2`, and IP content fill with
  DeepSeek.
- Keep unrelated runtime code untouched while staging each boundary.
- Ensure every code boundary has its matching `agent_chats` ledger entry.

Exit criteria:

- Each boundary has focused validation recorded in its ledger.
- No broad feature work starts before this worktree is packaged.

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
