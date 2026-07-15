# Timeline Spec v1 And Rendering Main Chain

## Status

This is the product and engineering contract for the timeline main chain. It is
normative for new work and reflects the current Timeline-first storage, API,
lineage, and render/export implementation. Transition surfaces still exist for
legacy data and compatibility paths.

Current implementation has transition data in:

- `scene_beats`: normalized source beats inside each scene.
- `episodes.extra_metadata.audio_timeline`: episode-level audio timeline built
  from scene dialogue audio and scene beats.
- `scripts.extra_metadata.storyboard.frames`: storyboard support output and
  legacy compatibility surface.

The current main chain is:

```text
dialogue audio -> Timeline Spec v1 clips -> storyboard support -> render jobs -> export
```

## Product Rule

Timeline is the single source of truth for an Episode's playable output. The
default production path is audio-first:

1. Generate or reuse scene dialogue audio.
2. Merge scene beats into an episode audio timeline.
3. Import that transitional audio timeline into Timeline Spec v1 clips.
4. Use storyboard frames as support assets for the visual track.
5. Render proxy/final outputs from a locked timeline version.

Storyboard is not the main orchestration source. It may display placeholders,
keyframes, shot context, and generated media, but final ordering, duration,
asset selection, render status, and export decisions belong to Timeline Spec v1.

Visual-first generation is not a v1 main-chain path. It can be explored later as
an import mode into Timeline Spec v1, but it must not create a parallel source
of truth.

## Source Precedence

When data disagrees, use this precedence:

1. `Timeline Spec v1`: final playable arrangement and render source.
2. `episodes.extra_metadata.audio_timeline.beats`: transition input generated
   from real scene audio and beat offsets.
3. `scene_beats`: scene-local source segments and audit trail.
4. `scripts.extra_metadata.storyboard.frames`: support view and compatibility
   output.

The import bridge must preserve references backward to `scene_beats` and
`audio_timeline` so regenerated clips can be traced, but consumers that need
the current episode output must read Timeline Spec v1.

## Timeline Spec v1

Timeline Spec v1 is episode-scoped. A timeline binds one episode, one base
script version, and one imported audio timeline version.

Required envelope fields:

- `spec_version`: `"timeline.v1"`.
- `timeline_id`: database id once persisted; absent or null before create.
- `episode_id`: owning episode id.
- `script_id`: script version used to build the timeline.
- `version`: integer timeline version, incremented on every save.
- `source_audio_timeline_version`: version copied from
  `episodes.extra_metadata.audio_timeline.episode_audio.version`.
- `fps`: default `24`.
- `resolution`: target canvas such as `"1080x1920"` or `"1280x720"`.
- `duration_ms`: total playable duration.
- `tracks`: ordered list of tracks.

Optional short-drama production metadata may live beside `tracks`:

- `production_context`: platform, region, language, aspect ratio, compliance,
  and business-goal assumptions used by the generated episode.
- `concept_test_pack`: draft hook/ad variants for operator review before scaling
  production.
- `short_drama_quality`: compact scores such as hook, conflict turn,
  cliffhanger, vertical readability, and compliance risk.
- `localization_exports`: source language plus planned subtitle/dub variants.
- `feedback_loop`: post-release metrics expected for manual or CSV import.

This metadata informs prompts, review gates, localization, and later feedback
analysis. It does not replace Timeline ordering, timing, render state, or export
state.

Minimum v1 track types:

- `dialogue`: audio clips from scene dialogue or episode audio.
- `video`: visual clips, keyframes, and generated video assets.
- `subtitle`: text clips aligned to dialogue/action timing.

Reserved extension track types:

- `bgm`
- `sfx`

These extension tracks are allowed in the spec, but they must not block the v1
main chain.

### Stable Clip Identity

Every clip must have a stable `clip_id`. The importer must derive it from:

```text
{track_type}_scene_{scene_id}_beat_{beat_id}_{ordinal:03d}
```

Examples:

- `dialogue_scene_501_beat_9001_001`
- `video_scene_501_beat_9001_001`
- `subtitle_scene_501_beat_9001_001`

If `beat_id` is unavailable, use `beat_unknown` and include the original
`source.ordinal`. Re-dub, re-cut, re-render, replacement clips, and provider
retries must not mutate the original `clip_id`; they add metadata such as
`clip_replacement_of`, `render_source_version`, or a new asset reference.

### Clip Fields

Required clip fields:

- `clip_id`
- `track_type`
- `ordinal`
- `scene_id`
- `beat_id`
- `start_ms`
- `end_ms`
- `duration_ms`
- `source`

Required source fields:

- `source.kind`: `scene_beat` | `audio_timeline_beat` | `storyboard_frame` |
  `manual`.
- `source.scene_id`
- `source.beat_id`
- `source.audio_timeline_version`
- `source.storyboard_frame_id` when created from or displayed in storyboard.

Required audit fields when available:

- `timing_source`: `tts_duration` | `scene_beat` | `manual` | `imported`.
- `voice_source`: `virtual_ip` | `derived` | `narrator` | `unknown`.
- `character_ids`
- `environment_id`
- `render_source_version`
- `clip_replacement_of`

Asset references should prefer `media_assets` ids whenever they are present.
During transition, clip `asset_ref` may still contain raw legacy URLs or object
locators; Timeline create/update/import/rollback and render completion sync
those locators into `media_assets` and `timeline_clip_assets` lineage where the
current code can resolve them.

Short-drama video clips may also include support metadata under `source_refs`:

- `vertical_visual_contract`: 9:16 mobile-safe framing and readability hints.
- `short_drama_quality`: clip role such as opening hook, conflict turn, or
  cliffhanger.
- `human_review`: operator gate status for script quality, compliance risk, and
  keyframe identity before expensive video generation.

### Timeline Shot Plan Prompt Bundle

Timeline video clips may carry a generated prompt bundle under
`clip.source_refs.timeline_shot_plan`. This bundle is support data for image,
video, storyboard-frame, and grid-storyboard generation. It must not replace
Timeline clip ordering, timing, duration, identity, render selection, or export
state.

New shot-plan generation uses a five-layer prompt method:

- `direction_anchor`: the shot's creative direction without locking the model to
  one fixed template.
- `aesthetic_reference`: objective visual references such as camera/lens, film
  stock, named production style, color pairing, or design era.
- `composition_geometry`: explicit screen-space relationships such as
  left/right/center, foreground/background, thirds, symmetry, or split lines.
- `motion_timeline`: two to four `{ "at_ms": int, "action": str }` beats inside
  the clip duration.
- `emotional_landing`: the final mood, rhythm, and light temperature of the
  shot.

The bundle also keeps compatibility fields such as `visual_prompt`,
`video_prompt`, `character_anchor`, `camera`, and `action`. Consumers must
fallback to those older fields when five-layer fields are absent, because older
Timeline rows and storyboard frames can still be valid.

Allowed shot-plan styles are `2d_cartoon`, `3d_cartoon`, and `live_action`.
`live_action` means believable human actors and real camera/lens language; it
does not make visual-first generation a v1 main-chain path.

### Minimal JSON Shape

```json
{
  "spec_version": "timeline.v1",
  "timeline_id": 123,
  "episode_id": 124,
  "script_id": 127,
  "version": 3,
  "source_audio_timeline_version": 2,
  "fps": 24,
  "resolution": "1080x1920",
  "duration_ms": 298000,
  "tracks": [
    {
      "track_id": "dialogue-main",
      "type": "dialogue",
      "clips": [
        {
          "clip_id": "dialogue_scene_501_beat_9001_001",
          "track_type": "dialogue",
          "ordinal": 1,
          "scene_id": 501,
          "beat_id": 9001,
          "start_ms": 0,
          "end_ms": 3200,
          "duration_ms": 3200,
          "audio_asset_id": 310,
          "text": "你终于回来了。",
          "timing_source": "tts_duration",
          "voice_source": "virtual_ip",
          "source": {
            "kind": "audio_timeline_beat",
            "scene_id": 501,
            "beat_id": 9001,
            "audio_timeline_version": 2
          }
        }
      ]
    },
    {
      "track_id": "video-main",
      "type": "video",
      "clips": [
        {
          "clip_id": "video_scene_501_beat_9001_001",
          "track_type": "video",
          "ordinal": 1,
          "scene_id": 501,
          "beat_id": 9001,
          "start_ms": 0,
          "end_ms": 3200,
          "duration_ms": 3200,
          "start_frame_asset_id": 111,
          "end_frame_asset_id": 112,
          "video_asset_id": 210,
          "timing_source": "tts_duration",
          "render_source_version": 3,
          "source": {
            "kind": "audio_timeline_beat",
            "scene_id": 501,
            "beat_id": 9001,
            "storyboard_frame_id": "frame-1",
            "audio_timeline_version": 2
          }
        }
      ]
    }
  ]
}
```

## Current Storage Model

The current storage model is:

- `timelines`: episode-scoped sequence rows with `spec`, `version`, status,
  rollback state, soft-delete state, user audit fields, and updated timestamps.
- `timeline_revisions`: immutable snapshots for persisted timeline versions,
  used by rollback without mutating older render outputs.
- `media_assets`: unified image/video/audio/subtitle asset rows used by clips
  and render jobs.
- `timeline_clip_assets`: clip-to-asset lineage keyed by stable `clip_id`,
  `timeline_version`, `asset_role`, and `media_asset_id`.
- `render_jobs`: proxy/final render attempts pinned to `timeline_id` and
  `timeline_version`, with idempotency by render type and preset hash.

Compatibility metadata in `episodes.extra_metadata.audio_timeline` and
`scripts.extra_metadata.storyboard.frames` remains readable, but new Timeline
work should write the tables above and treat raw URL fields as migration or
fallback locators.

## Import Bridge Contract

The current bridge endpoint remains:

```text
POST /api/v1/scripts/{script_id}/timeline-pipeline/generate-async
```

It is the compatibility entrypoint for generating dialogue audio, transitional
`audio_timeline`, Timeline Spec v1, and storyboard placeholders. The default
production script generation path and deprecated audio-timeline endpoint also
import `audio_timeline.beats` into Timeline Spec v1 as compatibility bridges.

Import rules:

- Preserve beat ordering by `start_ms`, then `scene_number`, then beat order.
- Create `dialogue` and `subtitle` clips only for spoken dialogue beats.
- Treat generic narrator fallback prose such as `冲突升级：` / `爽点：` /
  `卡点：` blocks as silent action timing even when legacy source data labels
  them as `dialogue`.
- Create `video` clips for dialogue, action, and intentionally preserved pause
  beats.
- Skip short pauses by default unless the audio pipeline already preserved them
  as storyboard-worthy beats.
- Use TTS-derived `start_ms/end_ms/duration_ms` as the default duration source.
- Copy `speaker_name`, `characters_involved`, `scene_id`, `scene_number`, and
  `beat_id` into clip source/audit fields.
- Write `source_audio_timeline_version` on the timeline envelope.
- Repair legacy imports when an existing Timeline has action, pause, or generic
  narrator fallback prose on `dialogue` / `subtitle` tracks for the same
  `source_audio_timeline_version`.

## Timeline API Contract

Implemented timeline APIs:

- `GET /api/v1/episodes/{episode_id}/timelines`: list timeline versions.
- `POST /api/v1/episodes/{episode_id}/timelines`: create an episode timeline.
- `GET /api/v1/timelines/{timeline_id}`: read timeline spec and render state.
- `PATCH /api/v1/timelines/{timeline_id}`: update with version lock.
- `POST /api/v1/timelines/{timeline_id}/shot-plan`: generate Timeline-native
  shot plans for video clips.
- `POST /api/v1/timelines/{timeline_id}/render`: queue proxy/final render job.
- `GET /api/v1/timelines/{timeline_id}/render-jobs`: list render attempts,
  including `output_asset` when a render succeeds.
- `GET /api/v1/timelines/{timeline_id}/resolved-videos`: list Timeline video
  clips with resolved playback URLs, missing reasons, and active generating task
  overlay for operator playback surfaces.
- `GET /api/v1/timelines/{timeline_id}/clip-assets`: list source, generated,
  replacement, and render-output lineage for Timeline clips.
- `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework`: record an
  existing media asset as re-dub, re-cut, or re-render lineage without changing
  the stable `clip_id`.
- `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework/video`: queue a
  provider-backed video rework task for a selected Timeline video clip.
- `DELETE /api/v1/timelines/{timeline_id}`: soft-delete a timeline with a
  version lock.
- `POST /api/v1/timelines/{timeline_id}/restore`: restore a soft-deleted
  timeline with a version lock.
- `POST /api/v1/timelines/{timeline_id}/rollback`: create a new current version
  from a prior `timeline_revisions` snapshot.
- `DELETE /api/v1/timelines/{timeline_id}/render-jobs/{render_job_id}`:
  soft-delete a render attempt with a timeline version lock.
- `POST /api/v1/timelines/{timeline_id}/render-jobs/{render_job_id}/restore`:
  restore a soft-deleted render attempt with a timeline version lock.

A dedicated `POST /api/v1/episodes/{episode_id}/timelines/import-audio` may be
added later, but current imports happen through generation bridges.

Write APIs must require `expected_version`. If the persisted version has moved,
return a version conflict rather than merging silently.

Render APIs must be idempotent for the same `timeline_id`, `timeline_version`,
`render_type`, and preset hash. Re-running the same render request should return
the existing queued/running/succeeded render job unless the caller explicitly
requests a new attempt.

`force_new_attempt=true` is only valid for failed or cancelled render jobs. It
soft-deletes the old active attempt and creates a fresh queued attempt for the
same timeline version and preset.

## Render Contract

Render jobs consume exactly one locked timeline version. They must not render a
mutable current draft.

When a stable `clip_id` has replacement lineage, render resolution must prefer
the latest active `generated_video` `timeline_clip_assets` link before falling
back to the original Timeline Spec asset reference or legacy storyboard video.
Provider rework success may enqueue a final render job for the same locked
Timeline version by adding a rework fingerprint to the render preset hash.

Render inputs:

- `timeline_id`
- `timeline_version`
- `render_type`: `proxy` | `final`
- `preset`: fps, resolution, bitrate, audio settings, subtitle mode.
- `force_new_attempt`: optional retry flag for failed/cancelled attempts.

Current render behavior:

- Resolve renderable video clips from Timeline video track, clip-asset
  replacement lineage, direct asset refs, or legacy storyboard frame videos.
- Expose the same video-source resolution through the read-only
  `resolved-videos` API so Timeline, storyboard support, and render readiness UI
  consume one playback read model instead of independently guessing URLs.
- Resolve Timeline dialogue audio from `source.episode_audio`, or resolve
  per-dialogue clip `asset_ref` URLs into audio segments and mix them by
  `start_ms`/`end_ms` before replacing the final video audio track with ffmpeg
  while preserving video duration.
- Resolve Timeline subtitle track into SRT cues and burn those cues into the
  proxy/final video with ffmpeg using an explicit CJK-capable font.
- Production lip-sync and full-episode dialogue pacing remain separate quality
  boundaries.

Render outputs:

- `render_jobs.status`
- `render_jobs.output_asset_id`
- `render_jobs.output_asset`
- `render_jobs.log`
- `media_assets` row for the proxy/final output.

Proxy output is for operator preview. Final output is the publish/download
artifact.

## Operator Workflow

The default user path is `Episode -> Timeline`. The timeline operator view must
surface:

- clip list ordered by start time;
- source audio and source beat;
- source frame/keyframe and generated video asset;
- render status, failure reason, retry, replace clip, and export;
- links back to storyboard support for visual context.

Storyboard remains a support view for placeholders, keyframes, and scene/shot
context. It must not become the primary route for render/export decisions.

### Clip Storyboard Support Mode

Storyboard is a selected-video-clip operation. After Timeline has video clips
and shot-plan prompt bundles, visual generation has two supported forms:

- start/end frame mode: generate per-clip first/last images, then generate each
  video clip from those keyframes;
- clip storyboard mode: generate a storyboard sheet for one selected Timeline
  `video` clip, then use the whole ordered sheet as visual reference for
  reworking that same clip.

The shot-plan LLM emits structured `motion_timeline` visual beats; it does not
choose an arbitrary free-form grid size. When the request omits `panel_count`,
backend policy maps distinct beats plus clip duration to 2/4/6/9 panels. Explicit
operator counts remain fixed after normalization to those supported layouts.

Clip storyboard sheets are support assets. They do not create, reorder, resize,
or replace Timeline clips, and they do not own render/export state. Store preview
metadata under `timeline.spec.support_views.clip_storyboards[clip_id]`, keep the
quick lookup on the selected clip as `clip.source_refs.clip_storyboard`, and
persist the sheet as a `media_assets` image with the `clip_storyboard_sheet`
role. Video clip rework may use the sheet as a provider reference through
`reference_mode="clip_storyboard_sheet"`. Its video prompt reads every panel
left-to-right and top-to-bottom as ordered action anchors, preserves the clip's
exact target duration, and explicitly suppresses the sheet borders, gutters,
panel numbers, and split-screen layout in the rendered video.

`reference_mode="clip_storyboard_panel"` remains readable for legacy tasks, but
new UI submissions default to the full-sheet sequence. Storyboard-sheet mode and
start/end-frame mode are alternative video reference paths; either one may make
a clip ready when its other gates pass.

Legacy `support_views.storyboard_grid`, `storyboard_grid_sheet`, and
`reference_mode="storyboard_grid_panel"` data may remain readable for existing
rows. New UI and API flows must not generate an episode-wide or Timeline-wide
storyboard sheet.

## Validation Contract

Minimum regression chain:

```text
scene audio -> episode audio_timeline -> Timeline Spec v1 -> storyboard support -> clip render -> export
```

Required checks for relevant changes:

- Timeline Spec schema validation.
- Import validation from `audio_timeline.beats`.
- Stable `clip_id` preservation across re-dub/re-render.
- Version-lock update conflict.
- Render job idempotency.
- Browser E2E for `Episode -> Timeline -> Render -> Export`.
