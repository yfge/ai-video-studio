## User Prompt

- "video_scene_91_beat_4003_013 这个任务 里，每一个宫格说明都是一致啊/？？"

## Goals

- Verify the concrete task data before changing code.
- Fix new Timeline clip storyboard tasks so panel briefs are not the same sentence repeated with only `Key moment N`.
- Preserve the selected-clip storyboard request shape and existing reference image/model fields.

## Changes

- Confirmed task `6066` / `Timeline clip storyboard - video_scene_91_beat_4003_013` had repeated panel prompts in persisted task `prompt` and `parameters.panels`.
- Added `clip_storyboard_panel_moments.py` with fallback panel moment profiles for clip storyboards that lack a detailed `motion_timeline`.
- Updated `build_clip_storyboard_panels()` so clip-text fallback panels now get distinct Opening / Interaction / Detail / Closing style briefs, motion timestamps, composition guidance, and emotional landing values.
- Added unit regression coverage for the exact `video_scene_91_beat_4003_013` style input.
- Added API task-payload coverage to ensure `/clips/{clip_id}/storyboard/generate` writes distinct panel prompts into task parameters.

## Validation

- Red check:
  - `cd ai-pic-backend && pytest tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py::test_build_clip_storyboard_panels_diversifies_clip_text_fallback -q`
  - Failed before implementation because current panels still contained `Key moment`.
- Green backend checks:
  - `cd ai-pic-backend && pytest tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py -q`
  - Passed: 5 tests.
  - `cd ai-pic-backend && pytest tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py tests/test_timeline_storyboard_grid_api.py::test_timeline_clip_storyboard_creates_generation_task_for_selected_clip_only -q`
  - Passed: 6 tests.
- Concrete clip reproduction:
  - Rebuilt panels from live timeline 69 clip `video_scene_91_beat_4003_013` using current code.
  - Resulting prompts were unique and mapped to Opening / Interaction / Detail / Closing frames with motion anchors at 36260, 38556, 40852, and 43148 ms.
- Contracts:
  - `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/storyboard/clip_storyboard_panel_moments.py ai-pic-backend/app/services/storyboard/grid_storyboard_prompt_bridge.py ai-pic-backend/tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py ai-pic-backend/tests/test_timeline_storyboard_grid_api.py`
  - Passed.

## Next Steps

- Existing task `6066` is already completed with the old prompt stored in the database; it will not mutate retroactively.
- Regenerate the clip storyboard after backend/worker code is reloaded to get the diversified panel briefs.

## Linked Commits

- None yet.
