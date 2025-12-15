---
id: 2025-12-15T12-21-55Z-storyboard-from-audio-timeline
date: 2025-12-15T12:21:55Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, storyboard, timeline]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/unit/test_dialogue_audio_service.py
  - tasks.md
summary: "Generate storyboard frame placeholders from episode audio_timeline beats"
---

## User Prompt

基于已生成的对白音轨与 episode 时间轴（beats），生成最终的分镜帧（先做结构占位），并保持原子提交、更新 tasks.md、补 agent_chats 记录。

## Goals

- 从 `episodes.extra_metadata.audio_timeline.beats` 生成分镜帧占位（dialogue/action + 长 pause）
- 写回 `scripts.extra_metadata.storyboard.frames`，并更新 `storyboard_version/storyboard_updated_at`
- 提供异步 API + Celery 入口，默认保护已有图像/视频资产（需 overwrite 才覆盖）

## Changes

- `ai-pic-backend/app/services/dialogue_audio_service.py`：新增 timeline→frames 的纯函数与落库函数（拒绝覆盖已有资产）
- `ai-pic-backend/app/schemas/generation.py`：为 `StoryboardFrame` 增加 `start_ms/end_ms` 字段，保留时间轴信息
- `ai-pic-backend/app/api/v1/endpoints/scripts.py`：新增 `POST /api/v1/scripts/{id}/storyboard/from-audio-timeline/generate-async` 与 Celery 处理函数
- `ai-pic-backend/app/services/task_worker.py`：注册新任务 `tasks.script_audio_storyboard_generate`
- `ai-pic-backend/tests/unit/test_dialogue_audio_service.py`：新增 unit test 覆盖 pause 过滤与 frame window 生成
- `tasks.md`：勾选“基于 beats/时间轴生成分镜帧占位”工作项

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`

## Next Steps

- 前端 Episode 页增加 3 个按钮入口与任务轮询展示（对白音轨/时间轴/分镜占位）
- Chrome 端到端走通：Episode → 生成对白音轨 → 生成时间轴 → 生成分镜帧，并记录到 agent_chats

## Linked Commits

- (pending)
