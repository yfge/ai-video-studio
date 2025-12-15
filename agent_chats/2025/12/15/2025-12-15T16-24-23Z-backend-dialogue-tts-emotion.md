---
id: 2025-12-15T16-24-23Z-backend-dialogue-tts-emotion
date: 2025-12-15T16:24:23Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tts, dialogue-audio]
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/tests/unit/test_dialogue_audio_service.py
  - tasks.md
summary: "Pass emotion/action into TTS for dialogue beats and persist normalized tts_emotion metadata."
---

## User Prompt

对白生成没有传入情绪参数。

## Goals

- 从剧本对白结构中提取 `emotion` / `action`，在调用 TTS 时带上情绪参数。
- 将归一化后的情绪信息随 beats 一并落库，便于后续时间轴/分镜消费与审计追溯。

## Changes

- `ai-pic-backend/app/services/dialogue_audio_service.py`：
  - 从 `script.dialogues` 提取 `emotion` / `action` 并在 segment 规划与生成阶段向下传递。
  - 新增情绪归一化 `_normalize_tts_emotion()`，仅输出提供商已知的有限情绪集合；无法识别则不传。
  - 调用 TTS 时传入 `emotion`，并将 `emotion` / `tts_emotion` / `action` 写入 `SceneBeat.extra_metadata`。
- `ai-pic-backend/tests/unit/test_dialogue_audio_service.py`：补充 emotion 映射与透传单测，覆盖 beats 规划与 TTS 调用参数。
- `tasks.md`：补充并勾选该修复项。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- 手工 Smoke：触发 `/api/v1/scripts/{id}/dialogue-audio/generate-async` 并检查 `/api/v1/story-structure/scenes/{scene_id}/beats` 返回的 `extra_metadata.tts_emotion` 已写入。

## Next Steps

- 与具体 TTS 提供商的 emotion 枚举做一次对齐（若有官方文档），补充映射表与回退策略说明。

## Linked Commits

- pending
