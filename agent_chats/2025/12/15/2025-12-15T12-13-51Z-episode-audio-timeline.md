---
id: 2025-12-15T12-13-51Z-episode-audio-timeline
date: 2025-12-15T12:13:51Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, audio, timeline]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/unit/test_dialogue_audio_service.py
  - tasks.md
summary: "Added episode-level audio concatenation and timeline generation persisted to episodes.extra_metadata"
---

## User Prompt

在对白音轨流程中，补齐“按 Episode 拼接场景音轨 + 合并/偏移 beats 形成 episode 时间轴”，并确保音频上传 OSS、按原子工作项更新 tasks.md 与提交。

## Goals

- 生成 episode 级对白音轨（按场景顺序拼接 scene 音频）并上传 OSS
- 合并 scene beats 并做时间偏移，产出 episode `audio_timeline` JSON 落到 `episodes.extra_metadata`
- 提供异步 API + Celery 任务入口，支持幂等跳过与 overwrite 重算

## Changes

- `ai-pic-backend/app/services/dialogue_audio_service.py`：新增 episode 级拼接与时间轴生成（拼接 mp3、合并 beats、回填 `episodes.extra_metadata.audio_timeline`）
- `ai-pic-backend/app/api/v1/endpoints/scripts.py`：新增 `POST /api/v1/scripts/{id}/audio-timeline/generate-async` 与 Celery 处理函数
- `ai-pic-backend/app/services/task_worker.py`：注册新任务 `tasks.script_audio_timeline_generate`
- `ai-pic-backend/tests/unit/test_dialogue_audio_service.py`：新增 unit test 覆盖 beats offset 合并逻辑
- `tasks.md`：勾选“按 Episode 拼接场景音轨”工作项

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`

## Next Steps

- 基于 episode `audio_timeline` 生成分镜帧占位（写入 `scripts.extra_metadata.storyboard.frames`）
- 前端 Episode 页补入口与任务进度展示，并在 Chrome 走通端到端用例

## Linked Commits

- (pending)
