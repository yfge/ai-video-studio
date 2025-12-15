---
id: 2025-12-15T17-01-45Z-backend-dialogue-strip-inline-actions
date: 2025-12-15T17:01:45Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tts, dialogue-audio]
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/tests/unit/test_dialogue_audio_service.py
  - tasks.md
summary: "Strip inline (action) from dialogue text so TTS doesn't read stage directions; use extracted action to infer tts_emotion."
---

## User Prompt

你如果生成的对白是有（动作)台词的，（动作）不应该被传入，而是转化成一种情绪进入另一个参数；现在听到的是“叹了一口气，站起来说 BLABLA”。

## Goals

- 将对白文本中的（动作）/“…说：”类口头说明从 TTS 文本中剥离，避免被朗读出来。
- 将剥离出的动作信息合并到 beats `action` 元数据，并用于推导 `tts_emotion` 传给 TTS。

## Changes

- `ai-pic-backend/app/services/dialogue_audio_service.py`：
  - 新增 `_sanitize_dialogue_content()`：剥离前后括号动作与“动作+说/问/答：”前缀，将动作合并到 `action` 字段，返回纯台词文本。
  - `script.dialogues` 提取阶段调用该清洗逻辑，确保 `seg.text`（即 TTS text）不包含动作。
  - 扩充 `_normalize_tts_emotion()`：支持从动作里识别 `低声/自语→whisper`、`叹气→sad` 等关键词。
- `ai-pic-backend/tests/unit/test_dialogue_audio_service.py`：新增对白清洗单测，并补充 action→emotion 映射断言。
- `tasks.md`：补充并勾选“对白文本中的（动作）不进入朗读”的修复项。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- API Smoke（登录 `geyunfei`）：
  - 触发 `POST /api/v1/scripts/17/dialogue-audio/generate-async`（`scene_numbers=[2,5]`，覆盖生成）
  - 检查 `GET /api/v1/story-structure/scenes/18/beats` / `.../scenes/21/beats`：
    - `dialogue_excerpt` 不再包含前缀括号动作
    - `metadata.action` 追加包含剥离出的动作文本
    - `metadata.tts_emotion` 分别为 `sad` / `whisper`（由 emotion/action 归一化得到）

## Next Steps

- 若后续需要更强的健壮性，可评估：是否也要剥离对白中间的括号动作（目前仅处理前后与“…说：”前缀，降低误伤概率）。

## Linked Commits

- pending
