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

### P1: Distinguish Identity-Bound And Identity-Free Storyboard Frames

Timeline-generated support frames can explicitly carry `characters: []` for
object, insert, and environment-only shots. Those frames do not need a character
identity reference, while frames with named characters still must not generate
without their bound references. Historical frames that omit `characters` remain
conservative and continue to require references.

Optimization:

- Treat an explicit empty `characters` list as an identity-free frame.
- Keep `require_reference_images=true` as the pipeline safety contract, but
  apply it per frame: identity-bound and legacy/unknown frames require a usable
  reference; identity-free frames may generate without one.
- Keep all eligible indexes in one child task so task lineage and progress remain
  stable.

Exit criteria:

- Queue tests prove an explicit identity-free frame is not skipped while a
  legacy frame with no character classification is still skipped.
- Processor tests prove the same task can enforce references for character
  frames and allow an explicit identity-free frame through without a reference.

### P1: Promote Generated Support Images Into Clip Asset Lineage

Timeline-derived storyboard frames already carry a stable `timeline_clip_id`,
but the historical storyboard image worker only wrote generated URLs back to
`scripts.extra_metadata.storyboard.frames`. Provider-backed clip video tasks
therefore could not reuse those generated images unless the Timeline Spec was
mutated by a separate keyframe workflow.

Optimization:

- After storyboard images are persisted, idempotently create/reuse `media_assets`
  and link each generated frame to `timeline_clip_assets` with role
  `storyboard_image`, source Timeline version, task id, and frame provenance.
- Keep the Timeline Spec and version unchanged; this is support-asset lineage,
  not an editorial timing change.
- Resolve clip-video start images from embedded Timeline refs first, then current
  and historical `storyboard_image` lineage for the same stable `clip_id`.

Exit criteria:

- Lineage tests prove generated support images are linked idempotently by stable
  clip id without incrementing Timeline version.
- Video rework API tests prove a clip with no embedded start-frame ref consumes
  its `storyboard_image` lineage URL as `image_url`.

### P1: Hydrate Missing Reference Context When Reusing Placeholders

A non-overwrite Timeline pipeline can reuse storyboard placeholders from the
same Timeline ID and version without rebuilding prompts or incrementing
`storyboard_version`. Reuse must not bypass newer character/environment binding
logic: legacy placeholders can otherwise keep empty `reference_images` and be
filtered out before paid image generation starts.

Optimization:

- Copy current placeholder frames and run reference-context enrichment without
  rewriting `prompt_description`, frame IDs, timing, or operator-selected refs.
- Backfill missing `speaker_name` and explicit character identity from the
  matching current Timeline video clip before enrichment, so older placeholders
  retain canonical character semantics without prompt-text inference.
- Persist the refreshed frames without incrementing `storyboard_version`, and
  only when enrichment changes the payload.
- Allow environment references to hydrate identity-free frames even when the
  story has no character visual registry.
- Queue image generation from the refreshed frame payload, not the stale
  pre-refresh list.

Exit criteria:

- A same-Timeline placeholder reuse test proves missing character refs are
  persisted and queued while frame ID, prompt, manual refs, and storyboard
  version remain unchanged.
- A reference-only enrichment test proves environment refs work without any
  character visuals and prompt text is not rewritten.
- The reuse path performs no text/image/video provider request.

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

- Declare `episode_timeline_beats.py` and `storyboard_from_timeline.py` the
  canonical beat and support-view builders.
- Keep `timeline_processor.py` only as a thin import-compatible wrapper; it must
  not own frame construction, prompt optimization, persistence, or timing logic.
- Retire its legacy storyboard-only duration resegmentation. Timeline/audio
  timing is authoritative, so a support view must not independently split or
  merge source windows.
- Export canonical builders directly from `app/services/audio/__init__.py`.
- Keep old tests only for compatibility-wrapper delegation, while canonical
  behavior remains covered at the canonical module paths.

Exit criteria:

- One canonical builder owns support-view generation.
- A source-contract test prevents application modules from importing
  `timeline_processor`; only the compatibility module and its focused tests may
  reference that path.

### P1: Make Storyboard Image Dispatch Idempotent While Active

Repeated Timeline or canvas execution can submit the same storyboard frame set
while its previous image task is still pending or processing. Creating another
Celery task for the same effective inputs risks duplicate provider charges and
competing writes to the same storyboard frames.

Optimization:

- Compute a versioned SHA-256 fingerprint from the user/script, selected frame
  snapshots, model and generation parameters, references, prompt override,
  canvas branch, and optional execution scope.
- Exclude mutable worker checkpoint outputs (`image_url`, generated keyframes,
  compiled prompt metadata, candidate lineage, and task checkpoint markers)
  while retaining every source prompt/reference field consumed by generation.
- Reuse a matching non-deleted `pending` or `processing`
  `STORYBOARD_IMAGE_GENERATION` task and do not dispatch Celery again.
- Keep terminal tasks retryable: `completed`, `failed`, and `cancelled` requests
  create a new task so explicit regeneration and recovery still work.
- Persist the full fingerprint in task parameters and verify it after the
  repository lookup rather than trusting a partial match.
- If Celery dispatch raises after task creation, mark the task `failed` with the
  dispatch error before returning the failure. A retry must not reuse an orphan
  `pending` row that was never dispatched.

Exit criteria:

- Repeating an identical request while its first task is active returns the
  same task ID, reports `status=reused`, and calls Celery exactly once.
- Changing a frame prompt, model, references, or execution scope creates a new
  request fingerprint and task.
- A first-frame checkpoint during an active multi-frame task does not change the
  request fingerprint or enqueue a duplicate batch.
- Failed/cancelled/completed tasks are not reused.
- A dispatch exception leaves the created task in `failed`, not `pending`.

### P1: Make Storyboard Video Dispatch Idempotent While Active

Repeated Production Canvas execution can enqueue the same image-to-video inputs
while the first parent task is pending or processing. Each duplicate parent can
fan out into another set of paid Seedance submissions.

Optimization:

- Compute a versioned SHA-256 fingerprint from the user/script, selected frame
  snapshots, resolved start images, model and video options, Timeline rework
  mapping, canvas branch, and target run scope.
- Reuse a matching active `VIDEO_GENERATION` parent task without dispatching a
  second Celery message; expose the reuse decision in the canvas skill output.
- Keep completed, failed, and cancelled requests retryable.
- Mark a newly persisted parent task `failed` if Celery dispatch raises, so a
  later retry cannot reuse work that never reached the worker.

Exit criteria:

- Identical active requests return the same task and dispatch exactly once.
- Changing the model, selected frame, or run scope creates a new task.
- All terminal statuses can be retried.
- Dispatch failure is durable as `failed` with the transport error recorded.

### P1: Checkpoint Paid Storyboard Video Submissions Per Frame

A multi-frame parent submits provider jobs sequentially. Deferring the database
commit until the whole loop finishes can lose an earlier paid provider task ID
if a later submission or failure-record write raises. Also, generated video
output fields must not alter an active request fingerprint while siblings are
still running.

Optimization:

- Commit each submitted or failed `VideoGenerationTask` child before starting
  the next provider request.
- Convert unexpected provider submission exceptions into durable failed child
  rows so the parent accounts for every requested frame.
- On a replay of the same parent, reuse an existing child for that frame and
  submit only missing children; explicit regeneration still uses a new parent.
- Do not mark the parent complete until child frame indexes cover every explicit
  frame requested in the parent payload.
- Fingerprint only the frame fields consumed by video submission, excluding
  mutable generated-video outputs such as `video_url` and `video_generation`.
- Keep provider inputs such as prompt, start/end images, references, duration,
  and Timeline rework mapping in the fingerprint.

Exit criteria:

- A later database failure cannot roll back an earlier provider task ID.
- A provider transport exception becomes a failed child while earlier submitted
  children remain pollable.
- Replaying a partially submitted parent does not call the provider again for
  already recorded frames.
- Polling one successful child cannot complete a two-frame parent.
- A sibling video result checkpoint does not create a duplicate active parent.
- Prompt, image, reference, duration, model, frame, or scope changes still
  produce a new request.

### P1: Checkpoint Paid Storyboard Images Per Frame

The storyboard image worker can generate many paid frames in one Celery task.
Persisting only after the final frame means a later provider error discards all
earlier successful results and their clip lineage even though those calls were
already billed.

Optimization:

- After each frame returns generated URLs, immediately persist the accumulated
  storyboard frame state.
- Record the completing task ID on each successful frame. If that same Celery
  task is replayed, remove completed frames before dynamic-prompt construction
  and provider submission so only missing frames incur work or cost.
- Sync that frame's image into stable Timeline clip lineage and commit before
  starting the next provider request.
- Keep the parent task failed when a later frame fails, while preserving every
  successful earlier image for targeted retry and downstream video generation.

Exit criteria:

- A two-frame regression proves frame 1 and its `storyboard_image` clip link are
  durable when frame 2 raises a provider error.
- Replaying the same failed two-frame task skips frame 1 and retries only frame
  2; it does not rebuild dynamic prompts or regenerate paid output for frame 1.
- Existing image persistence, reference enforcement, and identity-free tests
  remain green.

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
