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
- Commercial readiness still depends on legacy risk reduction and production
  sample evidence.

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
- [x] Implement backend re-dub, re-cut, and re-render replacement lineage around
      stable clip identity.
- [x] Add an operator read view for selected clip source/output/replacement asset
      history.
- [x] Add operator controls to record an existing `media_asset_id` as
      re-dub/re-cut/re-render replacement lineage for a selected clip.
- [x] Wire selected video clip re-cut/re-render into a provider-backed video
      generation task queue.
- [x] Persist successful provider video task output as `provider_rework`
      replacement lineage for the same stable `clip_id`.
- [x] Wire operator controls into the provider-backed rework task API.
- [x] Wire provider rework success into render queue orchestration.

Exit criteria:

- [x] Backend re-dub/re-cut/re-render replacement records do not change the
      original `clip_id`.
- [x] Backend API can show source audio, source frame, generated video, and output
      assets for a selected clip.
- [x] Operator UI can show source audio, source frame, generated video, output
      asset, and replacement history for a selected clip.
- [x] Operator UI can submit existing media assets as replacement lineage for a
      selected clip without changing the stable `clip_id`.
- [x] Backend API can queue provider-backed video rework for a selected stable
      `clip_id`.
- [x] Successful provider video tasks write `provider_rework` assets with
      `replacement_of_id` history.
- [x] Operator rework flows can request provider-backed regenerated assets from
      the UI while keeping the stable `clip_id` in request context.
- [x] Provider rework success can automatically enqueue the relevant
      render/export path.

Latest validation:

- `cd ai-pic-backend && pytest tests/test_timeline_clip_rework_api.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_api.py tests/test_timeline_import_service.py tests/test_timeline_lifecycle_api.py tests/test_timeline_spec_validation.py tests/unit/services/render/test_timeline_render_service.py tests/unit/services/video/test_video_task_polling_service.py tests/unit/services/video/test_video_task_generation_metadata.py -q`
- Result: passed, 29 tests, 1 skipped.
- `cd ai-pic-frontend && npm run test`
- Result: passed, 19 tests.
- `cd ai-pic-frontend && npm run lint`
- Result: passed with 0 errors and 18 existing warnings.
- `cd ai-pic-backend && pytest tests/test_timeline_clip_rework_api.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_video_rework_render_queue.py tests/test_timeline_api.py tests/test_timeline_import_service.py tests/test_timeline_lifecycle_api.py tests/test_timeline_spec_validation.py tests/unit/services/render/test_timeline_render_service.py tests/unit/services/render/test_timeline_render_rework_assets.py tests/unit/services/video/test_video_task_polling_service.py tests/unit/services/video/test_video_task_generation_metadata.py -q`
- Result: passed, 31 tests, 1 skipped.
- Codex built-in Browser evidence:
  `artifacts/runs/frontend-provider-rework-controls-iab-20260525T100147Z/browser-validation.json`
  and
  `artifacts/runs/frontend-provider-rework-controls-iab-20260525T100147Z/timeline-provider-rework-controls.png`.
  The run opened the Timeline workspace, selected a video clip, filled the
  provider rework form, and confirmed the submit button was visible and enabled.
  It did not submit the form to avoid queueing a real provider task in the local
  development environment.
- `timeline_clip_assets` now records clip-to-asset lineage by stable `clip_id`.
  Timeline create/update/import/rollback sync source assets from Timeline Spec,
  and render success records output assets per rendered clip.
- `GET /api/v1/timelines/{timeline_id}/clip-assets` exposes lineage entries for
  future operator audit views.
- `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework` records
  re-dub/re-cut/re-render replacement assets against the same stable `clip_id`
  with optimistic version locking and `replacement_of_id` history.
- The Timeline operator inspector now calls
  `GET /api/v1/timelines/{timeline_id}/clip-assets?timeline_version=<version>`
  and shows selected-clip asset role, locator, source, render job, and
  replacement history.
- The Timeline operator inspector now posts existing media asset replacements to
  `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework` and refreshes
  the selected-clip asset audit view.
- `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework/video` now
  creates a provider-backed video generation parent task for selected clip
  rework, preserving the locked Timeline version and stable `clip_id`.
- The Timeline operator inspector now exposes provider-backed video rework
  controls for selected video clips and posts to
  `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework/video`.
- Video task polling now applies successful `timeline_rework` outputs as
  `provider_rework` clip assets, with `replacement_of_id` history against the
  previous generated video role.
- Timeline render resolution now prefers the latest `generated_video` clip asset
  lineage for a stable `clip_id`, so provider rework replacements become render
  inputs without changing the Timeline Spec clip identity.
- Provider rework success now queues a final render job when the submitted
  rework context has `auto_render=true`. The render preset carries a rework
  fingerprint so a prior final render for the same Timeline version does not
  block the new render through idempotency.
- `dialogue_audio_service.py` is now a compatibility facade: storyboard timeline
  placeholder conversion, scene audio generation, episode concatenation, beats
  persistence, and episode/storyboard timeline helpers live under
  `app.services.audio.*`.
- Episode audio timeline concatenation and persistence now live behind
  `app.services.audio.episode_audio_builder`, with episode beat construction in
  `app.services.audio.episode_timeline_beats`; `dialogue_audio_service.py`
  remains a compatibility import surface for those helpers. Scene-level TTS
  generation and beat persistence are still the remaining split target.
- Scene beat persistence, scene audio metadata writeback, and per-scene duration
  validation now live in `app.services.audio.scene_audio_persistence`; historical
  imports no longer own the implementation.
- Duration-controlled dialogue generation and the deprecated dialogue-audio API
  endpoint now call `app.services.audio.scene_audio_generator` directly for
  scene-level audio generation, keeping the historical service out of those
  production entry points.
- Duration-controlled per-scene generation now lives in
  `app.services.duration_controlled_scene_runner`, and the touched deprecated
  dialogue-audio endpoint now uses repository helpers instead of direct
  SQLAlchemy queries.
- Historical dialogue-audio fixed segment planning and text cleanup compatibility
  now live in `app.services.audio.dialogue_service_compat` and
  `app.services.audio.dialogue_service_text_compat`, keeping the old service file
  below the service-size limit.
- `scripts_legacy.py` no longer owns the shared script task-title formatter:
  legacy regeneration and the split audio/timeline pipeline endpoints now use
  `app.services.script.task_titles`. The cleanup also removed unused
  URL/UUID/datetime helpers from the legacy router.
- The backend mock AI service now returns schema-matched responses for script
  cliffhanger judgement and script quality-gate repair, so the script generation
  API test exercises the current quality-gate path instead of failing on a
  generic scoring payload.
- Static script catalog routes for `/scripts/formats` and `/scripts/languages`
  now live in `app.api.v1.endpoints.scripts_catalog` and are mounted inside the
  legacy router before dynamic `/{script_id}` routes.
- `ai_service_manager.py` request/prompt/response logging and shared truncation
  now live in `app.services.ai_manager_logging`; the manager keeps wrapper
  methods for existing callers such as video task dispatching.
- `ai_service_manager.py` model-list cache keying, lookup, and writes now live
  in `app.services.ai_manager_model_cache`, keeping provider enumeration in the
  manager while isolating cache behavior.
- `ai_service_manager.py` provider rate-limit checks, explicit preference,
  priority selection, weighted selection, and request-count increments now live
  in `app.services.ai_manager_provider_selection`; the manager keeps compatibility
  wrappers.
- `ai_service_manager.py` shared failure response construction for unavailable
  providers, no-fallback exceptions, provider-prefixed errors, and terminal
  fallback failures now lives in `app.services.ai_manager_failure_responses`.
- `ai_service_manager.py` model listing aggregation now lives in
  `app.services.ai_manager_model_listing`, covering model-list cache reuse,
  enabled-provider filtering, capability-based model type matching, and stable
  sorting.
- `ai_service_manager.py` text generation fallback orchestration now lives in
  `app.services.ai_manager_text_generation`, including provider pinning,
  default text model resolution, JSON/schema parameter pass-through, and logging.
- `ai_service_manager.py` text, image, image-to-image, and video default model
  resolution now lives in `app.services.ai_manager_model_resolution`, shared by
  the focused provider orchestration helpers.
- `ai_service_manager.py` generated image URL/base64 normalization and OSS upload
  now lives in `app.services.ai_manager_image_assets`; the manager keeps the
  compatibility wrapper used by existing generation paths.
- `ai_service_manager.py` text-to-image fallback orchestration now lives in
  `app.services.ai_manager_image_generation`, including style spec resolution,
  OpenAI style normalization, provider logging, and success image OSS conversion.
- `ai_service_manager.py` image-to-image fallback orchestration now lives in
  `app.services.ai_manager_image_to_image`, including reference preload,
  provider attempts, success image OSS conversion, and text-to-image fallback.
- `ai_service_manager.py` image-to-image reference preloading, HTTPS-to-HTTP
  download normalization, inline compression, and data URL construction now live
  in `app.services.ai_manager_image_assets`.
- `ai_service_manager.py` image-to-image fallback-to-text-to-image provider
  inference, prompt construction, and fallback metadata now live in
  `app.services.ai_manager_image_fallback`.
- `ai_service_manager.py` text-to-image and image-to-image style spec
  resolution, prompt injection, OpenAI style derivation, and style metadata
  attachment now live in `app.services.ai_manager_image_style`.
- `ai_service_manager.py` video generation fallback orchestration now lives in
  `app.services.ai_manager_video_generation`, including provider selection,
  default video model resolution, request/response logging, and terminal failure
  response construction.
- `ai_service_manager.py` text-to-speech fallback orchestration now lives in
  `app.services.ai_manager_tts_generation`, including provider selection,
  request/response logging, and terminal failure response construction.
- `ai_service_manager.py` provider status payload construction and provider
  config updates now live in `app.services.ai_manager_provider_status`.

## Phase 6: Produce Ten Narrow Samples

Tracker: `docs/cartoon-sample-production-proof.md`.

Tasks:

- [x] Pick one narrow vertical and 2-3 reusable characters.
- Produce 10 vertical samples, each 30-60 seconds.
- Record cost, generation time, failure points, manual fixes, selected models,
  output file, and reusable prompt/workflow decisions.

Current fixed scope:

- Use stylized 2D/3D cartoon visual prompts, not live-action or realistic human
  imagery, to avoid provider safety restrictions becoming the dominant signal.
- Micro-genre: workplace fantasy reversal with light suspense.
- Reusable cast: Lin Xia, Kai, and the non-human assistant Momo.

Exit criteria:

- At least 10 exported samples exist with production metrics.
- The team can identify which parts of the workflow are repeatable and which
  still require manual intervention.
- Follow-up tasks are based on production evidence, not platform expansion.
