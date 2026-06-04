## User Prompt

PLEASE IMPLEMENT THIS PLAN: Fix Action Beats Entering Dialogue Audio Tracks.

The reported live case was script 128 / Timeline 64, where a stage-direction paragraph was present in dialogue, video, and subtitle tracks and the dialogue clip carried an episode_audio asset_ref.

## Goals

- Keep action and pause beats available for video/storyboard timing.
- Prevent action and pause beats from becoming dialogue clips or subtitle clips.
- Repair the existing live Timeline for script 128 without regenerating scene TTS.
- Validate the live storyboard workspace after repair.

## Changes

- Updated `ai-pic-backend/app/services/timeline_spec_builder.py` so Timeline Spec import builds dialogue and subtitle tracks from dialogue beats only.
- Kept the video track built from all normalized beats, preserving dialogue, action, and pause visual timing coverage.
- Adjusted `ai-pic-backend/tests/test_timeline_import_service.py` fixture coverage to include dialogue, action, and pause beats.
- Updated test expectations so action and pause beats only appear in the video track, while dialogue asset lineage only counts true dialogue clips.
- Repaired live Timeline 64 through `PATCH /api/v1/timelines/64` with version lock, filtering existing dialogue/subtitle clips without starting any TTS or audio generation task.

## Validation

- Source-level builder behavior check:
  - Command: bundled Python executed `timeline_spec_builder.py` source after stripping only the model type import.
  - Result: `builder_filter_ok {'dialogue': 1, 'video': 3, 'subtitle': 1}`.
- Targeted pytest:
  - Command: `cd ai-pic-backend && .venv/bin/python -m pytest tests/test_timeline_import_service.py -v`
  - Result: timed out after 60 seconds with no test output. A prior faulthandler probe showed the local `.venv` hanging during `import pytest`, before entering project tests.
- Backend quick suite:
  - Command: `cd ai-pic-backend && .venv/bin/python run_tests.py quick`
  - Result: timed out after 90 seconds with no output, consistent with the same local Python/pytest import hang.
- Live repair:
  - Timeline 64 moved from version 10 to version 11.
  - Before repair: dialogue track had 12 dialogue, 2 pause, and 3 action clips; subtitle track had 12 dialogue and 3 action clips.
  - After repair: dialogue track has 12 dialogue clips only; subtitle track has 12 dialogue clips only; video track still has 12 dialogue, 2 pause, and 3 action clips.
  - The reported action paragraph is absent from dialogue and subtitle tracks and remains in the video track as `video_scene_561_beat_3843_003` with no `asset_ref`.
- Evidence files:
  - `artifacts/runs/20260604-action-beat-dialogue-audio/timeline-api-validation.json`
  - `artifacts/runs/20260604-action-beat-dialogue-audio/browser-page-validation.json`
  - `artifacts/runs/20260604-action-beat-dialogue-audio/storyboard-v11.png`

## Next Steps

- Re-run `tests/test_timeline_import_service.py -v` and `python run_tests.py quick` after the local `.venv` pytest import hang is resolved.

## Linked Commits

- This commit.
