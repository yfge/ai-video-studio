---
id: 2026-01-31T10-15-00Z-frame-duration-splitter-phase2
date: 2026-01-31T10:15:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, storyboard, video-duration-alignment, refactor]
related_paths:
  - ai-pic-backend/app/services/storyboard/frame_duration_splitter.py
  - ai-pic-backend/tests/unit/services/storyboard/test_frame_duration_splitter.py
  - ai-pic-backend/app/services/audio/timeline_processor.py
  - ai-pic-backend/tasks.md
summary: "Implemented Phase 2 video-duration-alignment: frame duration splitter for storyboard generation"
---

## User Prompt

继续 (Continue from previous session)

## Goals

1. Fix failing test `test_slightly_over_max_split` in frame_duration_splitter
2. Integrate frame_duration_splitter into timeline_processor.py
3. Update tasks.md to mark Phase 2 items complete
4. Create agent_chats ledger entry

## Changes

### 1. `tests/unit/services/storyboard/test_frame_duration_splitter.py`

- Fixed `test_slightly_over_max_split` test by adding `min_duration_seconds=0.0` parameter
- This disables the absorption threshold for tiny segments, allowing the test to verify that frames slightly over max ARE split when there's no minimum duration constraint

### 2. `app/services/audio/timeline_processor.py`

- Added imports for frame_duration_splitter functions and constants
- Fixed `datetime.utcnow()` deprecation: replaced with `datetime.now(timezone.utc)`
- Updated `utc_now_iso()` to use timezone-aware datetime
- Extended `generate_storyboard_from_episode_audio_timeline()` with new parameters:
  - `max_frame_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS` (8.0s)
  - `min_frame_duration_seconds: float = DEFAULT_MIN_DURATION_SECONDS` (4.0s)
  - `adjust_durations: bool = True`
- Integrated `adjust_frame_durations()` call after building raw frames from audio timeline
- Added `duration_adjustment` audit info to storyboard metadata

### 3. `tasks.md`

- Marked Phase 2 tasks as complete:
  - [x] 后端：从 audio_timeline 生成 storyboard 时，按 `max_allowed_duration_seconds` 在 beat 边界拆分长镜头
  - [x] 后端：为拆分/合并后的 frame 写入 stable linkage

## Validation

### Unit Tests

```bash
python -m pytest tests/unit/services/storyboard/test_frame_duration_splitter.py -v
# Result: 21 passed

python -m pytest tests/unit/services/audio/test_timeline_processor.py -v
# Result: 25 passed

python -m pytest tests/unit/services/storyboard/ -v -q
# Result: 123 passed
```

### Implementation Details

The frame_duration_splitter module provides:

1. **`split_long_frames()`**: Splits frames exceeding `max_duration_seconds` (default 8.0s) into segments at beat boundaries
   - Creates linkage metadata: `parent_frame_id`, `split_index`, `total_splits`, `beat_range`
   - Adds "（续）" marker to continuation segments
   - Absorbs very short final segments (< 50% of min_duration) into previous segment

2. **`merge_short_frames()`**: Merges consecutive short frames of mergeable types (pause, action)
   - Respects scene boundaries (different scenes are not merged)
   - Respects timeline continuity (gaps in timeline prevent merging)
   - Dialogue beats are not merged by default
   - Tracks merged beat IDs for auditing

3. **`adjust_frame_durations()`**: Combined function that first merges short frames, then splits long frames

### Integration Flow

```
build_storyboard_frames_from_audio_timeline()
    → adjust_frame_durations() [NEW]
        → merge_short_frames()
        → split_long_frames()
    → apply_storyboard_prompt_optimizations()
    → persist to script.extra_metadata
```

## Next Steps

1. E2E verification: Test with a >8s frame to confirm splitting works end-to-end
2. Chrome verification: Navigate to storyboard page and verify split frames display correctly
3. Consider adding UI indicators for split/merged frames

## Linked Commits

(To be committed)
