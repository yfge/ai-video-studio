---
id: 2025-12-15T12-02-29Z-scene-dialogue-audio
date: 2025-12-15T12:02:29Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, audio, scene]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/unit/test_dialogue_audio_service.py
  - tasks.md
summary: "Added async scene-level dialogue audio generation (OSS upload + scene_beats persistence)"
---

## User Prompt

实现“对白音轨与声音驱动时间轴”特性：先完成按场景生成对白音轨（1 scene = 1 track）、scene 级 `scene_beats` 落库，并要求所有音频上传 OSS、保持原子提交与 tasks.md 更新。

## Goals

- 提供可异步触发的“按 script 生成场景对白音轨 + scene_beats”入口，支持跳过已生成结果与覆盖重跑
- 产出可复用的 segment 规划逻辑（对白/动作/停顿），并补齐无对白场景的静音占位
- 补齐单测覆盖纯逻辑部分，保证 pytest quick gate 可持续通过

## Changes

- 新增 `ai-pic-backend/app/services/dialogue_audio_service.py`：场景级对白音轨生成（TTS + 静音段拼接）、上传 OSS、落库 `SceneBeat` 并写回 `Scene.metadata.dialogue_audio`
- 新增 `POST /api/v1/scripts/{script_id}/dialogue-audio/generate-async`：创建任务并由 Celery 执行批量场景生成
- 新增 Celery 任务 `tasks.script_dialogue_audio_generate` 并在 worker 中实现进度写回
- 新增单测 `ai-pic-backend/tests/unit/test_dialogue_audio_service.py` 覆盖 segment 规划与留白兜底
- 更新 `tasks.md` 勾选“按场景生成对白混音音轨”工作项

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`

## Next Steps

- 实现 episode 级音轨拼接与 `episodes.extra_metadata.audio_timeline` 生成（含 OSS 上传）
- 基于时间轴生成分镜帧占位（写入 `scripts.extra_metadata.storyboard.frames`，避免误覆盖已有图像资产）
- 前端 Episode 页增加一键入口与任务进度展示，并补 Chrome E2E 路径记录

## Linked Commits

- (pending)
