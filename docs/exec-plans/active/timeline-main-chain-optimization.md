# Timeline Main Chain Optimization Review

## Scope

This review checks the current script -> timeline -> storyboard generation chain
after the Timeline Spec v1 import bridge landed.

Reviewed path:

```text
production script generation
-> scene dialogue audio
-> episodes.extra_metadata.audio_timeline
-> timelines.spec
-> scripts.extra_metadata.storyboard.frames
-> Episode Timeline workspace
```

This document began as an optimization plan. The P0-P2 ownership alignment
slice is implemented. Render/export execution, first-class clip asset lineage,
provider-backed clip video rework, and rework-triggered final render queueing are
also implemented. Real API and provider-chain harness evidence now proves
Timeline-first ordering with explicit `dialogue`, `video`, and `subtitle` tracks
before media generation. Subtitle burn-in and Timeline dialogue audio replacement
have focused render proof. Commercial readiness still depends on provider cost,
stability, lip-sync, character consistency, and production quality evaluation at
sample scale.

## Current Chain Check

The default production path is now wired into Timeline Spec v1:

- `app.services.script.generation_task_persistence` passes `user_id` into
  `run_auto_timeline_placeholders`.
- `production_storyboard.py` generates scene dialogue audio when needed,
  builds episode `audio_timeline`, imports it into Timeline Spec v1, then
  generates storyboard support placeholders from Timeline Spec clips.
- `timeline_pipeline.py` and deprecated `audio_timeline.py` also import
  existing or newly generated `audio_timeline.beats` into Timeline Spec v1.
- `audio_storyboard.py` remains available as a deprecated compatibility path
  and marks output as legacy audio-timeline support view.
- `useEpisodeMetadata.ts` asks `/episodes/{episode_id}/timelines` first and
  falls back to `episodes.extra_metadata.audio_timeline` only when no matching
  Timeline Spec is available.
- `EpisodeTimelineWorkspaceModel.ts` builds tracks from native Timeline Spec
  before using the legacy audio-timeline adapter.
- `backfill_timeline_specs.py` can dry-run or apply Timeline Spec imports for
  older episodes.

No immediate blocker was found in the default production chain. Downstream
execution now has worker and output-asset plumbing, and a real harness flow can
render/export a Timeline whose clips resolve to legacy storyboard videos.
First-class clip asset lineage now has backend source/output/rework records,
operator controls for existing media assets, and a provider-backed video rework
task path that records successful outputs as replacement lineage. Operator-side
provider rework entry is implemented, and provider success can queue a final
render job with a rework fingerprint.

## Implementation Status

- P0 contract alignment is implemented: the public `clip_id` grammar uses the
  underscore form, clips carry `source.kind=audio_timeline_beat`, specs include
  default `fps`, `resolution`, and persisted `timeline_id`, and importer tests
  assert the stored row output.
- P1 ownership alignment is implemented for readiness and support views:
  workbench summaries read the latest Timeline row first, and default
  production/timeline-pipeline storyboard support generation reads Timeline Spec
  clips while deprecated storyboard-from-audio remains legacy.
- P2 frontend/backfill alignment is implemented: the workspace accepts native
  Timeline Spec tracks, task metadata includes Timeline references, and the
  backfill command is dry-run by default.
- P3 render/export execution is implemented, with passing legacy bridge real API
  E2E evidence in
  `artifacts/runs/main-chain-e2e-lineage-20260525T040437Z/golden_path.json` and
  provider-backed Timeline-first evidence in
  `artifacts/runs/provider-chain-dialogue-tracks-smoke-20260526T033733Z/provider_chain.json`.
- P4 backend lineage is implemented for Timeline Spec assets, render outputs,
  and operator/provider replacement records keyed by stable `clip_id`.
- Operator asset audit, existing-media rework controls, and provider-backed
  video rework controls are implemented for selected Timeline clips. Backend
  provider-backed video rework queueing and success lineage are implemented,
  and provider success queues a final render job whose preset is keyed to the
  replacement asset. The render worker now resolves/concatenates video clips,
  replaces source episode audio, mixes per-dialogue clip audio by Timeline
  timing, and burns Timeline subtitle cues with CJK font support.
- Full-30s provider-backed Timeline-first evidence is recorded in
  `artifacts/runs/provider-chain-dialogue-segments-full-30s-20260526T045229Z/provider_chain.json`.
  The CJK subtitle-font rerender is recorded in
  `artifacts/runs/provider-chain-dialogue-segments-full-30s-20260526T045229Z/subtitle_font_rerender.json`
  with output
  `https://resource.lets-gpt.com/timeline-renders/video/20260526/051434/7849fd70.mp4`.
  Subsequent provider-chain harness runs automatically save render ffprobe
  output and one extracted frame per Timeline scene after render success.
  Production lip-sync, character consistency, and sample production remain
  separate proof targets.

## Findings

### P0: Align Timeline Spec Contract And Import Shape

The spec document and importer previously described clip identity and clip
source fields differently.

Implemented alignment:

- `timeline_spec_builder.py` produces ids such as
  `dialogue_scene_11_beat_101_001`.
- Clips now carry `source.kind`, `source.scene_id`, `source.beat_id`, and
  `source.audio_timeline_version`.
- `source_refs` remains only as a compatibility alias during transition.
- Generated specs include default `fps=24`, `resolution=1080x1920`, and the
  persisted `timeline_id`.

Decision for this implementation slice:

- `docs/timeline-rendering-pipeline.md` uses the current underscore grammar:
  `dialogue_scene_501_beat_9001_001`.
- Clip provenance is described as `source.kind`, `source.scene_id`,
  `source.beat_id`, and `source.audio_timeline_version`.
- Asset references should ultimately point at `media_assets` ids rather than
  raw URLs.

Optimization:

- Choose one `clip_id` grammar and update both docs and tests to lock it.
- Add `source` while preserving `source_refs` only as a compatibility alias
  during transition.
- Add default `fps`, `resolution`, and `timeline_id` once persisted.
- Add a schema-level validation test that asserts the importer output matches
  the normative contract, not only the current Python helper.

Exit criteria:

- `test_timeline_import_service.py` checks the exact public clip id grammar.
- Import tests assert `source.kind == "audio_timeline_beat"` and keep
  `source_refs` only as a backward-compatibility field.

### P1: Make Readiness Checks Read Timeline Rows

Workbench and story production readiness previously inferred "timeline ready"
from `episodes.extra_metadata.audio_timeline`.

Observed consumers:

- `workbench_service.py`
- `StoryProductionModel.ts`

That could show a timeline-ready state when only the transitional audio
timeline existed, or miss newer `timelines.spec` rows if the legacy metadata
was stale.

Optimization:

- Add a backend summary/read model that checks the latest non-deleted
  `Timeline` row for the episode and selected script.
- Return timeline id, version, status, and `source_audio_timeline_version` in
  workbench/story production summaries.
- Keep legacy `audio_timeline` readiness only as a fallback while old episodes
  are being backfilled.

Exit criteria:

- Workbench summary tests cover an episode with Timeline Spec but no
  `audio_timeline` metadata.
- Story production UI displays timeline readiness from Timeline Spec when both
  sources disagree.

### P1: Move Storyboard Support Generation To Timeline Clips

The default storyboard support path now reads Timeline Spec clips. The legacy
audio-timeline builder remains available for compatibility and deprecated
entrypoints.

Optimization:

- Add `generate_storyboard_support_from_timeline_spec`.
- Use dialogue/video clips as the source of timing and provenance.
- Preserve `storyboard_frame_id` or create a stable `support_view.frame_id`
  mapping on the corresponding video clip.
- Continue writing `scripts.extra_metadata.storyboard.frames` as the support
  view until the UI is fully native Timeline Spec.

Exit criteria:

- New tests prove support frames are generated from Timeline Spec when present.
- Deprecated audio-timeline storyboard endpoint remains a compatibility path
  and explicitly marks `source_role=legacy_audio_timeline_support_view`.

### P1: Consolidate Storyboard Timeline Builders

There are multiple implementations that can build storyboard frames from an
audio timeline:

- `app/services/audio/storyboard_from_timeline.py`
- `app/services/audio/timeline_processor.py`
- deprecated compatibility builders in `app/services/audio/timeline_processor.py`

The active endpoints use `storyboard_from_timeline.py`, while tests still cover
old builders and `app/services/audio/__init__.py` exports the older
`timeline_processor` functions.

Optimization:

- Declare `storyboard_from_timeline.py` the canonical support-view builder.
- Move any unique duration adjustment or prompt behavior from old builders into
  the canonical module if still needed.
- Stop exporting old storyboard builders from `app/services/audio/__init__.py`.
- Keep old tests only for compatibility wrappers, not as primary behavior.

Exit criteria:

- One canonical builder owns support-view generation.
- Contract checks or tests prevent new call sites from importing the old
  builders.

### P2: Give Frontend A Native Timeline Workspace Model

The frontend previously converted Timeline Spec dialogue clips into an
`audio_timeline`-shaped object so the existing timeline view could render.

That bridge hid Timeline Spec fields from the operator surface and kept the
workspace model coupled to legacy `beats`.

Optimization:

- Thread `selectedTimelineSpec` from `useEpisodeMetadata` into
  `EpisodeTimelineWorkspace`.
- Build tracks directly from `timeline.spec.tracks`.
- Render dialogue, video, subtitle, storyboard support, and render status from
  the native spec shape.
- Keep the `audio_timeline` adapter only as a fallback adapter named
  `legacyAudioTimelineToTimelineTracks`.

Exit criteria:

- `EpisodeTimelineWorkspaceModel` accepts a Timeline Spec input first.
- UI tests cover Timeline Spec present, Timeline Spec absent with legacy
  fallback, and mismatched script id.

### P2: Make Task And Agent-Run Metadata Timeline-Aware

Task agent run builders previously summarized timeline/storyboard work mostly
through `audio_timeline_version` and `generation_method=audio_timeline`.

Implemented alignment:

- Add `timeline_id`, `timeline_version`,
  `source_audio_timeline_version`, and `source_role` to generated task metadata.
- For render/export phases, still add `render_job_id`, `render_type`, and
  `output_asset_id` in P3.

Exit criteria:

- Task detail and agent-run summaries can link directly to the Timeline Spec
  and, later, render job.

### P2: Backfill Existing Episodes

The bridge now writes Timeline Spec during generation, but older episodes may
only have `audio_timeline`.

Implemented alignment:

- Add an admin/backfill command that scans episodes with matching
  `audio_timeline.script_id` and no latest Timeline row.
- Import with `overwrite=false` and record skipped, created, failed, and
  script-mismatch counts.
- Keep the command dry-run by default.

Exit criteria:

- Backfill can be run in dry-run mode without mutating rows.
- A targeted test covers stale/mismatched script ids.

### P3: Render And Export Implementation

Current render APIs enqueue idempotent `render_jobs`; the Timeline render worker
now consumes queued jobs, blocks stale or incomplete timelines, and writes
successful outputs to `media_assets`.

Optimization:

- [x] Implement render worker for proxy/final output.
- [x] Resolve clip assets through Timeline Spec, storyboard support frames, and
      `media_assets`.
- [x] Write output to `media_assets` and set `render_jobs.output_asset_id`.
- [x] Refuse to render if the requested `timeline_version` no longer matches
      the locked row.

Exit criteria:

- Re-running the same render request returns the same queued/running/succeeded
  job.
- Completed render outputs do not mutate older timeline versions.

## Recommended Sequence

1. Contract alignment: clip id grammar, `source` fields, default envelope
   fields, schema validation.
2. Readiness alignment: workbench/story production summary reads Timeline rows.
3. Storyboard support alignment: generate support view from Timeline Spec when
   available.
4. Builder consolidation: one canonical support-view builder and compatibility
   wrappers only where needed.
5. Frontend native model: render tracks from Timeline Spec, keep legacy adapter
   only as fallback.
6. Backfill: import old audio timelines into Timeline Spec with dry-run first.
7. Render/export: consume locked timeline versions and persist media assets.

Steps 1-7 are implemented for this slice. Delete/rollback, stricter Timeline
Spec validation, backend first-class clip asset lineage, provider-backed video
rework success lineage, operator provider-rework entry, and rework-triggered
render queue orchestration are also implemented. The next boundary is legacy
debt reduction and production sample validation.

## Validation Matrix

Backend:

- `pytest tests/test_timeline_import_service.py -q`
- `pytest tests/integration/test_timeline_pipeline_import_api.py -q`
- `pytest tests/unit/services/script/test_production_storyboard_timeline_import.py -q`
- Readiness tests cover workbench and story summaries reading Timeline rows.
- Support-view tests cover storyboard generation from Timeline Spec.

Frontend:

- `cd ai-pic-frontend && npm run lint`
- Focused tests cover native Timeline Spec track building and legacy fallback.
- Real API E2E covers `Episode -> Timeline -> Render -> Export` with a script
  that has renderable legacy storyboard video clips.

Repo checks:

- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `git diff --check`

## Resolved Decisions

- The public `clip_id` grammar keeps the current underscore form:
  `{track_type}_scene_{scene_id}_beat_{beat_id}_{ordinal:03d}`.
- Timeline rows continue to use the current single-row, incrementing-version
  model for each `episode_id + script_id` pair.
- Storyboard support frames remain under `scripts.extra_metadata.storyboard`
  for this slice.

## Remaining Question

- Should storyboard support frames move into a first-class support-view table
  once render/export and media-asset output are complete?
- Which narrow vertical should be used for the first 10 production samples after
  the main chain has real E2E evidence?
