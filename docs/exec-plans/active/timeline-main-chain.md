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
- Phase 4 render/export execution and Phase 5 operator UI/harness paths are
  packaged, with one passing real API E2E run through a legacy storyboard video
  migration bridge and provider-backed Timeline-first harness evidence.
- P0-P2 ownership alignment is implemented: importer output matches the
  underscore `clip_id` contract, readiness checks prefer Timeline rows,
  storyboard support generation prefers Timeline Spec clips, the workspace can
  build native Timeline tracks, and a dry-run backfill command exists.
- Timeline delete/restore, rollback, schema/import validation, first-class clip
  asset lineage, backend rework replacement records, provider-backed video
  rework task lineage, operator provider rework controls, and rework-triggered
  render queue orchestration are implemented.

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

- [x] Browser/API evidence is stored under `artifacts/runs/<run_id>/`.
- Actual browser engine is recorded; Playwright fallback is not claimed as
  Chrome verification.
- [x] The selected script has renderable video clips, and the final render job
      reaches `succeeded` with `output_asset.file_url` or `output_asset.file_path`.

## Current Evidence

- `artifacts/runs/main-chain-e2e-lineage-20260525T040437Z/golden_path.json`
  records a passing `timeline_export_end_to_end` run against the local backend.
- The run rendered Timeline `2` version `1`; render job `3` succeeded with
  `output_asset.file_url` populated.
- `artifacts/runs/provider-chain-timeline-first-full-30s-20260525T181523Z/provider_chain.json`
  records a provider-backed 30s run where `timeline-create` happened before
  OpenAI image generation and Seedance video generation; Timeline `15` was
  updated from seed version `1` to asset version `2` and render job `20`
  succeeded.
- `artifacts/runs/provider-chain-dialogue-tracks-smoke-20260526T033733Z/provider_chain.json`
  records the stricter provider-backed smoke run where the Timeline seed has
  `dialogue`, `video`, and `subtitle` tracks before media generation; render job
  `21` succeeded.
- The current render worker still consumes video clips only. The provider-backed
  evidence proves Timeline-first structured lineage, not burned-in subtitles or
  TTS dialogue in final output.
- Commercial-readiness sequencing is tracked separately in
  `docs/exec-plans/active/main-chain-commercial-readiness.md`.
