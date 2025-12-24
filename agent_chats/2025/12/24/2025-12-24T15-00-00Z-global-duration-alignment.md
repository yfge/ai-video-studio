---
id: 2025-12-24T15-00-00Z-global-duration-alignment
date: 2025-12-24T15:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, timeline, duration, script-generation]
related_paths:
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/audio/dialogue_processor.py
  - ai-pic-backend/app/services/timeline_agent/agent.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/prompts/templates/episode_from_outline.yaml
  - ai-pic-backend/app/prompts/templates/episode_enrich.txt
  - ai-pic-backend/app/prompts/templates/episode_enrich.yaml
  - ai-pic-backend/app/prompts/templates.py
summary: "Implement global duration alignment from script generation through timeline to storyboard"
---

## User Prompt

"从剧本生成到时间轴再到分镜，要和剧集规划的时间对齐！！！"

User's key requirement: Episode planned for 3 minutes should result in 3-minute content throughout the pipeline - from script generation, to dialogue audio, to timeline, to storyboard. This must be embedded from the source, NOT post-processing scaling.

Additional request: "额外加上，如果剧本预估时间不够，就进行剧本丰富" (if script estimated time is insufficient, enrich the script).

## Goals

1. Embed duration constraints at script generation time
2. Pass target duration through dialogue generation
3. Validate timeline duration after aggregation
4. Enable end-to-end duration alignment from episode.duration_minutes

## Changes

### Phase 1: Script Generation Duration Constraints

**`ai-pic-backend/app/prompts/templates/episode_from_outline.yaml`**:
- Added explicit duration requirements in the prompt:
  - Target duration in seconds
  - Require `estimated_duration_seconds` for each scene
  - Validate scene durations sum to target (±15% tolerance)
  - Time distribution guidelines (opening 15-20%, middle 60-70%, climax 15-25%)
- Added `total_estimated_duration_seconds` to output format example

**`ai-pic-backend/app/prompts/templates.py`**:
- Added `EPISODE_ENRICH` template enum for duration enrichment

**`ai-pic-backend/app/prompts/templates/episode_enrich.txt` & `.yaml`**:
- New prompt template for enriching episode content when duration is insufficient
- Provides 5 enrichment strategies (add scenes, expand scenes, add transitions, deepen interactions, add emotional buildup)
- Requires marking new scenes with `is_new: true`

**`ai-pic-backend/app/services/episode_agent.py`**:
- Added duration validation constants:
  - `DURATION_TOLERANCE_LOW = 0.85`
  - `DURATION_TOLERANCE_HIGH = 1.15`
  - `DEFAULT_SCENE_DURATION_SECONDS = 30`
  - `MAX_ENRICH_ATTEMPTS = 2`
- Added helper functions:
  - `_calculate_episode_duration()`: Sum scene durations
  - `_validate_episode_duration()`: Check against target
- Added enrichment loop in `episodes_node`:
  - After episode validation, check if duration meets target
  - If insufficient, call `EPISODE_ENRICH` template up to 2 times
  - Log enrichment progress and final duration status

### Phase 2: Dialogue Generation Duration Parameter

**`ai-pic-backend/app/services/timeline_agent/agent.py`**:
- Added `target_duration_seconds` parameter to `compute_timing()`
- Pass through to initial state for LangGraph workflow
- Enhanced `_build_reasoning_prompt()` to include duration constraints
- Added duration constraint section in prompt when target provided

**`ai-pic-backend/app/services/audio/dialogue_processor.py`**:
- Added `target_duration_seconds` parameter to `plan_scene_segments_intelligent()`
- Pass to `TimelineLangGraphAgent.compute_timing()`

**`ai-pic-backend/app/services/dialogue_audio_service.py`**:
- Added `target_duration_seconds` parameter to `generate_scene_dialogue_audio()`
- Pass to `plan_scene_segments_intelligent()`

**`ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`**:
- Calculate `per_scene_target_seconds` from `episode.duration_minutes`
- Pass to both calls of `generate_scene_dialogue_audio()`
- Evenly distribute episode duration across scenes

### Phase 3: Timeline Duration Validation

**`ai-pic-backend/app/services/dialogue_audio_service.py`** (in `generate_episode_audio_timeline()`):
- Added duration validation after `build_episode_timeline_beats()`
- Log validation results with:
  - Target vs actual duration
  - Duration ratio
  - Whether within ±15% tolerance
- Warn if duration too short or too long

## Validation

1. Python syntax check passed for all modified files
2. Template loading verified - `EPISODE_ENRICH` template renders correctly
3. Backend pytest passes (1 pre-existing unrelated failure)
4. Frontend npm run lint passes (only pre-existing warnings)

## Next Steps

1. Phase 4: Full end-to-end testing with real episode generation
2. Consider adding database column for `estimated_duration_seconds` on Scene model
3. Monitor logs for duration validation results in production
4. Fine-tune enrichment strategies based on actual content gaps

## Linked Commits

- 07111df feat(timeline): implement global duration alignment from script to storyboard
