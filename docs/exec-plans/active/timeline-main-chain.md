# Timeline Main Chain

## Goal

Complete the production main chain:

```text
dialogue audio -> Timeline Spec v1 -> clip render -> export
```

This plan starts after the docs/spec-only pass that freezes the contract in
`docs/timeline-rendering-pipeline.md` and
`docs/dialogue-audio-timeline-spec.md`.

Current status:

- Phase 1 docs/spec-only baseline is complete.
- Phase 2 DB/API foundation is implemented with models, migration, timeline
  APIs, render job APIs, version locking, access filtering, and idempotent
  enqueue tests.
- Phase 3 import bridge is implemented for explicit one-click generation,
  default production script generation, and deprecated audio-timeline
  compatibility.
- Phase 4 render/export execution and Phase 5 operator UI/harness paths exist in
  the current worktree, but still need packaging and real browser/API evidence
  before the main chain is treated as production-ready.
- P0-P2 ownership alignment is implemented: importer output matches the
  underscore `clip_id` contract, readiness checks prefer Timeline rows,
  storyboard support generation prefers Timeline Spec clips, the workspace can
  build native Timeline tracks, and a dry-run backfill command exists.

## Phase 1: Spec And Contracts

- Keep `Timeline Spec v1` as the episode output SSOT.
- Treat `episodes.extra_metadata.audio_timeline` as transition input only.
- Treat `scripts.extra_metadata.storyboard.frames` as support view and legacy
  compatibility output only.
- Document target `media_assets`, `timelines`, and `render_jobs` relationships.

Exit criteria:

- Repo docs checks pass.
- Tasks board marks only docs/spec progress, not implementation completion.

## Phase 2: DB And API Foundation

- [x] Add `timelines`, `media_assets`, and `render_jobs` models, repositories,
      schemas, and Alembic migration.
- [x] Add timeline list/read/update APIs with version locking.
- [x] Add render-job enqueue/read APIs with idempotency by timeline version and
      preset hash.

Exit criteria:

- Unit/API tests cover version conflict, permission checks, and idempotent
  render enqueue.

## Phase 3: Import Bridge

- [x] Extend the existing
      `/api/v1/scripts/{script_id}/timeline-pipeline/generate-async` path so it can
      import `audio_timeline.beats` into Timeline Spec v1.
- [x] Import production `auto_timeline_pipeline` and deprecated
      `/audio-timeline/generate-async` outputs into Timeline Spec v1.
- [x] Generate stable `clip_id` values from `track_type + scene_id + beat_id +
ordinal`.
- [x] Preserve source references to `scene_beats` and `audio_timeline` version.
- [x] Generate storyboard support views from Timeline Spec clips on the default
      production and timeline-pipeline paths.
- [ ] Preserve storyboard frame ids where available when storyboard support
      views are linked back into Timeline Spec clips.

Exit criteria:

- Regression test proves import creates dialogue, video, and subtitle clips with
  monotonic timing and stable clip ids.

## Phase 4: Render And Export

- Link existing storyboard image/video outputs to `media_assets`.
- Link storyboard support frame ids back into Timeline Spec video clips where
  available.
- [x] Render proxy/final outputs from a locked timeline version.
- [x] Persist render output as `media_assets` and `render_jobs.output_asset_id`.

Exit criteria:

- Focused render tests prove retry/idempotency and that completed outputs do not
  mutate older timeline versions.

## Phase 5: Operator UI And E2E

- [x] Build the workspace timeline tracks from native Timeline Spec with legacy
      `audio_timeline` fallback.
- [x] Make `Episode -> Timeline` the primary operator surface for clip status,
      video material state, render status, retry, replace entry, and export.
- [x] Keep storyboard as the visual support view for replace clip v1.
- [x] Add a standard E2E harness path for `Episode -> Timeline -> Render -> Export`.

Exit criteria:

- Browser evidence is stored under `artifacts/runs/<run_id>/`.
- Actual browser engine is recorded; Playwright fallback is not claimed as
  Chrome verification.
- The selected script has renderable video clips, and the final render job
  reaches `succeeded` with `output_asset.file_url` or `output_asset.file_path`.

## Current Evidence Gap

- The render/export implementation has targeted test coverage, but the real
  `Episode -> Timeline -> Render -> Export` run still needs to succeed against a
  local backend and a script with video clip assets.
- Commercial-readiness sequencing is tracked separately in
  `docs/exec-plans/active/main-chain-commercial-readiness.md`.
