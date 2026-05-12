# Dialogue Audio Timeline Transition Spec

## Status

This spec describes the existing audio-first transition layer that feeds
Timeline Spec v1. It is not the final source of truth for episode output.

Current storage:

- Scene audio metadata lives in `scenes.metadata.dialogue_audio`.
- Scene-local segments live in `scene_beats`.
- Episode-level merged audio lives in `episodes.extra_metadata.audio_timeline`.
- Storyboard placeholders live in `scripts.extra_metadata.storyboard.frames`.

Target source of truth:

- `Timeline Spec v1` as defined in `docs/timeline-rendering-pipeline.md`.

## Scope

The audio pipeline creates a deterministic bridge from script text to timeline
clips:

```text
scripts.dialogues/stage_directions
  -> scene dialogue audio
  -> scene_beats
  -> episodes.extra_metadata.audio_timeline.beats
  -> Timeline Spec v1 clips
  -> storyboard.frames support output
```

`audio_timeline` remains a compatibility and import payload. New render/export
work must consume Timeline Spec v1 after the import bridge exists.

## Input Sources

- `scripts.dialogues[]`: ordered dialogue source with `scene_number`,
  `character`, and `content`.
- `scripts.stage_directions[]`: action/pause source with `scene_number`,
  `content`, and optional timing hints.
- `scenes`: normalized scenes for the script, ordered by `scene_number`.
- Story/IP bindings: used to resolve voices and character audit metadata.

## Voice Binding

For Virtual IP roles:

- If `virtual_ips.voice_config` is missing, the pipeline may choose a `voice_id`
  from configured candidates and persist it to `virtual_ips.voice_config`.

For derived roles:

- A derived role is a script character that cannot map to the story's
  `StoryCharacter.virtual_ip_id`.
- The selected voice binding scope may be `scene`, `episode`, or `story`.
- Store scoped bindings in the closest existing JSON metadata:
  - `scenes.metadata.derived_character_voice_bindings`
  - `episodes.extra_metadata.derived_character_voice_bindings`
  - `stories.extra_metadata.derived_character_voice_bindings`

## Scene Audio And Beats

Each scene produces one dialogue audio track. The track concatenates dialogue,
action, and pause segments in scene order.

Segment types:

- `dialogue`: TTS output for spoken content.
- `action`: silence or future environment audio for stage direction/action.
- `pause`: silence between dialogue segments.

Default timing:

- Dialogue duration comes from generated TTS audio.
- Dialogue pause defaults to 300 ms.
- Action silence defaults to 800 ms and may scale by text length.
- Empty scenes produce a 2 second action beat.

Scene audio metadata:

- `oss_url`
- `duration_seconds`
- `generated_at`
- `version`
- `script_id`

Required `scene_beats` fields:

- `scene_id`
- `order_index`
- `beat_type`: `dialogue` | `action` | `pause`
- `dialogue_excerpt`
- `beat_summary`
- `duration_seconds`
- `metadata.start_ms`
- `metadata.end_ms`
- `metadata.speaker_name`
- `metadata.speaker_kind`: `virtual_ip` | `derived` | `narrator`
- `metadata.voice_config`
- `metadata.source`: `dialogue_audio_pipeline`

`scene_beats` are the scene-local source segments. They are not the final
episode timeline because their times are local to each scene.

## Episode Audio Timeline

The episode audio timeline concatenates scene audio in scene order and offsets
scene-local beats into episode time.

Episode audio metadata:

- `script_id`
- `episode_audio.oss_url`
- `episode_audio.duration_seconds`
- `episode_audio.generated_at`
- `episode_audio.version`
- `beats[]`

Required beat fields:

- `scene_id`
- `scene_number`
- `beat_id`
- `beat_type`
- `speaker_name`
- `characters_involved`
- `dialogue_action`
- `dialogue_emotion`
- `text`
- `start_ms`
- `end_ms`

`episodes.extra_metadata.audio_timeline` is a transition payload. It is the
required input for importing Timeline Spec v1, but it must not be used as the
render/export source after the import exists.

## Mapping To Timeline Spec v1

Each eligible `audio_timeline.beats[]` item imports into matching Timeline Spec
v1 clips.

Dialogue beats:

- Create one `dialogue` clip with `audio_asset_id` once the scene/episode audio
  has a `media_assets` row.
- Create one `subtitle` clip using `text`, `start_ms`, and `end_ms`.
- Create one `video` placeholder clip with the same timing.

Action beats:

- Create one `video` placeholder clip.
- Create one `subtitle` clip only when visible text or operator notes are
  needed.

Pause beats:

- Skip by default when shorter than the storyboard minimum pause threshold.
- Import when the beat is intentionally preserved as visual time.

Stable `clip_id` format:

```text
{track_type}:scene-{scene_id}:beat-{beat_id}:ord-{ordinal}
```

Mapping rules:

- `start_ms/end_ms/duration_ms` come from `audio_timeline.beats`.
- `timing_source` is `tts_duration` for dialogue and `scene_beat` for action or
  imported pauses unless manually edited later.
- `voice_source` comes from beat metadata when present.
- `source.kind` is `audio_timeline_beat`.
- `source.audio_timeline_version` is copied from
  `episode_audio.version`.
- The timeline envelope `source_audio_timeline_version` uses the same version.

## Storyboard Support Output

`storyboard.frames` remains a compatibility output and support view.

Allowed usage:

- Show visual placeholders derived from beats.
- Hold generated prompt descriptions, reference images, and frame/video legacy
  URLs during the transition.
- Link back to Timeline Spec clips through `scene_id`, `beat_id`, timing fields,
  and optional `storyboard_frame_id`.

Disallowed usage:

- Do not treat storyboard frame order or duration as the final render/export
  source once Timeline Spec v1 exists.
- Do not rely on storyboard frame index as clip identity.

## Validation Requirements

The import bridge must validate:

- every imported clip has stable `clip_id`;
- clip timing is monotonic and non-negative;
- total timeline duration matches the episode audio duration within tolerance;
- `source_audio_timeline_version` is present;
- source beat references can be traced back to `scene_beats` when `beat_id`
  exists.
