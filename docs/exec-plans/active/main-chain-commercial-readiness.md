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
- Phase 2 has one passing real API harness run. It uses a legacy storyboard video
  migration bridge, not a finished first-class clip asset lineage system.
- Commercial readiness still depends on first-class clip asset lineage and
  production sample evidence.

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

- [x] Choose or create one script whose Timeline video clips resolve to actual video
      assets or storyboard frame videos.
- [x] Run the real `Episode -> Timeline -> Render -> Export` path through the
      operator flow or golden-path harness.
- [x] Store evidence under `artifacts/runs/<run_id>/`, including the actual browser
      engine or fallback.

Exit criteria:

- [x] A render job reaches `succeeded`.
- [x] `render_jobs.output_asset` exposes a usable `file_url` or `file_path`.
- [x] The evidence proves the route used a locked Timeline version.

Latest passing attempt:

- `python scripts/harness/run_golden_path.py --scenario timeline_export_end_to_end --run-id main-chain-e2e-lineage-20260525T040437Z --api-url http://localhost:8000 --base-url http://localhost:8089 --username geyunfei --password '<redacted>' --script-id 117 --timeout-seconds 900`
- Evidence: `artifacts/runs/main-chain-e2e-lineage-20260525T040437Z/golden_path.json`.
- Result: passed.
- Task `5989` completed, Timeline `2` version `1` was rendered, render job `3`
  reached `succeeded`, and output asset `1` exposed
  `https://resource.lets-gpt.com/timeline-renders/video/20260525/040535/7220b9a3.mp4`.
- The run used script `117` because it has legacy storyboard video assets. The
  import bridge created a Timeline video track from those frames after the old
  audio timeline was found to be non-monotonic.

## Phase 3: Add Timeline Delete And Rollback

Tasks:

- [x] Add safe delete/restore semantics for timelines and render attempts using the
      existing soft-delete pattern.
- [x] Add rollback to a prior timeline version without mutating the old render
      outputs.
- [x] Surface rollback state clearly in Timeline API responses.

Exit criteria:

- [x] API tests cover delete, restore, rollback, permission checks, and stale version
      conflicts.
- [x] Existing render jobs remain traceable after rollback.

Latest validation:

- `cd ai-pic-backend && pytest tests/test_timeline_api.py tests/test_timeline_lifecycle_api.py tests/test_timeline_import_service.py -q`
- Result: passed, 8 tests.
- `timeline_revisions` now stores immutable Timeline version snapshots. Rollback
  creates a new current Timeline version from an older snapshot and leaves
  existing render jobs addressable by their original `timeline_version`.
- `audio_timeline` import create/update paths also record Timeline revisions, so
  imported Timelines can later roll back.
- `alembic heads` reports `a4f5c6d7e8f9` as the current head.
- Full temp-SQLite `alembic upgrade head` is still blocked before this migration
  by existing migration `e5f3948ee82e`, which performs a SQLite-incompatible
  column-type alteration on `images.filename`.

## Phase 4: Harden Timeline Spec Validation

Tasks:

- [x] Add schema validation for Timeline Spec v1 envelope, tracks, clips, source
      fields, timing, and asset references.
- [x] Validate imports from `audio_timeline.beats` before persistence.
- [x] Make invalid specs fail with actionable errors instead of later render-time
      failures.

Exit criteria:

- [x] Tests reject malformed tracks, missing `clip_id`, non-monotonic timing, and
      invalid source references.
- [x] Import tests prove dialogue/video/subtitle clips preserve stable identity and
      provenance.

Latest validation:

- `cd ai-pic-backend && pytest tests/test_timeline_api.py tests/test_timeline_lifecycle_api.py tests/test_timeline_import_service.py tests/test_timeline_spec_validation.py -q`
- Result: passed, 15 tests.
- Timeline create/update/import/rollback now validate the same Timeline Spec v1
  envelope, clip timing, source references, and asset reference shape before
  persistence.
- Invalid API specs return HTTP 400 with structured `code`, `path`, and
  `message` details.

## Phase 5: Finish Clip Asset Lineage And Rework Actions

Tasks:

- [x] Treat start frames, end frames, storyboard images, storyboard videos, and final
      clip videos as first-class clip assets.
- [x] Link assets to stable `clip_id` values rather than temporary frame indexes.
- Implement re-dub, re-cut, and re-render around stable clip identity.

Exit criteria:

- Re-dub/re-cut/re-render do not change the original `clip_id`.
- [x] Backend API can show source audio, source frame, generated video, and output
      assets for a selected clip.
- Operator UI can show source audio, source frame, generated video, output asset,
  and replacement history for a selected clip.

Latest validation:

- `cd ai-pic-backend && pytest tests/test_timeline_api.py tests/test_timeline_import_service.py tests/test_timeline_lifecycle_api.py tests/test_timeline_spec_validation.py tests/unit/services/render/test_timeline_render_service.py -q`
- Result: passed, 20 tests.
- `timeline_clip_assets` now records clip-to-asset lineage by stable `clip_id`.
  Timeline create/update/import/rollback sync source assets from Timeline Spec,
  and render success records output assets per rendered clip.
- `GET /api/v1/timelines/{timeline_id}/clip-assets` exposes lineage entries for
  future operator audit views.

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
