# Timeline Spec v1 And Rendering Main Chain

## Status

This is the product and engineering contract for the timeline main chain. It is
normative for new work, but it is not a claim that all storage, API, or render
paths already exist.

Current implementation has transition data in:

- `scene_beats`: normalized source beats inside each scene.
- `episodes.extra_metadata.audio_timeline`: episode-level audio timeline built
  from scene dialogue audio and scene beats.
- `scripts.extra_metadata.storyboard.frames`: storyboard support output and
  legacy compatibility surface.

The target main chain is:

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
{track_type}:scene-{scene_id}:beat-{beat_id}:ord-{ordinal}
```

Examples:

- `dialogue:scene-501:beat-9001:ord-1`
- `video:scene-501:beat-9001:ord-1`
- `subtitle:scene-501:beat-9001:ord-1`

If `beat_id` is unavailable, use `beat-missing` and include the original
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

Asset references are always ids into the target `media_assets` table, not raw
URLs. During transition, raw legacy URLs may be stored inside `source.legacy`,
but new consumers should prefer asset ids.

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
          "clip_id": "dialogue:scene-501:beat-9001:ord-1",
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
          "clip_id": "video:scene-501:beat-9001:ord-1",
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

## Target Storage Model

The eventual storage model is:

- `timelines`: episode-scoped sequence rows with `spec`, `version`, status,
  user audit fields, and updated timestamps.
- `media_assets`: unified image/video/audio/subtitle asset rows used by clips
  and render jobs.
- `render_jobs`: proxy/final render attempts pinned to `timeline_id` and
  `timeline_version`.

No implementation may treat this section as already completed. Until the tables
exist, bridge code can keep writing transition metadata, but docs and new
interfaces should point at this target contract.

## Import Bridge Contract

The current bridge endpoint remains:

```text
POST /api/v1/scripts/{script_id}/timeline-pipeline/generate-async
```

It is the compatibility entrypoint for generating dialogue audio, transitional
`audio_timeline`, and storyboard placeholders. The next implementation slice
must add an import step that produces Timeline Spec v1 from
`audio_timeline.beats`.

Import rules:

- Preserve beat ordering by `start_ms`, then `scene_number`, then beat order.
- Create matching dialogue, video, and subtitle clips for each dialogue/action
  beat.
- Skip short pauses by default unless the audio pipeline already preserved them
  as storyboard-worthy beats.
- Use TTS-derived `start_ms/end_ms/duration_ms` as the default duration source.
- Copy `speaker_name`, `characters_involved`, `scene_id`, `scene_number`, and
  `beat_id` into clip source/audit fields.
- Write `source_audio_timeline_version` on the timeline envelope.

## API Contract To Implement Later

Target timeline APIs:

- `GET /api/v1/episodes/{episode_id}/timelines`: list timeline versions.
- `POST /api/v1/episodes/{episode_id}/timelines/import-audio`: import current
  `audio_timeline` into Timeline Spec v1.
- `GET /api/v1/timelines/{timeline_id}`: read timeline spec and render state.
- `PATCH /api/v1/timelines/{timeline_id}`: update with version lock.
- `POST /api/v1/timelines/{timeline_id}/render`: queue proxy/final render job.

Write APIs must require `expected_version`. If the persisted version has moved,
return a version conflict rather than merging silently.

Render APIs must be idempotent for the same `timeline_id`, `timeline_version`,
`render_type`, and preset hash. Re-running the same render request should return
the existing queued/running/succeeded render job unless the caller explicitly
requests a new attempt.

## Render Contract

Render jobs consume exactly one locked timeline version. They must not render a
mutable current draft.

Render inputs:

- `timeline_id`
- `timeline_version`
- `render_type`: `proxy` | `final`
- `preset`: fps, resolution, bitrate, audio settings, subtitle mode.

Render outputs:

- `render_jobs.status`
- `render_jobs.output_asset_id`
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

## Validation Contract

Minimum future regression chain:

```text
scene audio -> episode audio_timeline -> Timeline Spec v1 -> storyboard support -> clip render -> export
```

Required checks once implementation starts:

- Timeline Spec schema validation.
- Import validation from `audio_timeline.beats`.
- Stable `clip_id` preservation across re-dub/re-render.
- Version-lock update conflict.
- Render job idempotency.
- Browser E2E for `Episode -> Timeline -> Render -> Export`.
