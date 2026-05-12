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
- Phase 3 import bridge, Phase 4 real render/export execution, and Phase 5
  operator UI remain pending.

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

- Extend the existing
  `/api/v1/scripts/{script_id}/timeline-pipeline/generate-async` path so it can
  import `audio_timeline.beats` into Timeline Spec v1.
- Generate stable `clip_id` values from `track_type + scene_id + beat_id +
ordinal`.
- Preserve source references to `scene_beats`, `audio_timeline` version, and
  storyboard frame ids where available.

Exit criteria:

- Regression test proves import creates dialogue, video, and subtitle clips with
  monotonic timing and stable clip ids.

## Phase 4: Render And Export

- Link existing storyboard image/video outputs to `media_assets`.
- Render proxy/final outputs from a locked timeline version.
- Persist render output as `media_assets` and `render_jobs.output_asset_id`.

Exit criteria:

- Focused render tests prove retry/idempotency and that completed outputs do not
  mutate older timeline versions.

## Phase 5: Operator UI And E2E

- Make `Episode -> Timeline` the primary operator surface for clip status,
  source audio, source frames, render status, retry, replace, and export.
- Keep storyboard as the visual support view.
- Add a standard browser E2E for `Episode -> Timeline -> Render -> Export`.

Exit criteria:

- Browser evidence is stored under `artifacts/runs/<run_id>/`.
- Actual browser engine is recorded; Playwright fallback is not claimed as
  Chrome verification.
