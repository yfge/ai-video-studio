---
id: 2025-12-16T04-42-20Z-backend-storyboard-pause-merge
date: 2025-12-16T04:42:20Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, storyboard, timeline, audio]
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/tests/unit/test_dialogue_audio_service.py
  - tasks.md
summary: "Merge short pause beats into storyboard frames so per-scene storyboard duration matches dialogue audio."
---

## User Prompt

对白生成后，一个场景内对白时长与分镜总时长不一致。

## Goals

- 分镜时长严格服从音轨（声音优先定时长），scene 内分镜总时长与对白音轨一致。
- 保持帧数量可控：短 pause 不单独生成帧，而是合并进相邻帧。

## Changes

- `ai-pic-backend/app/services/dialogue_audio_service.py`：`build_storyboard_frames_from_audio_timeline` 将 `< min_pause_duration_ms` 的 pause beat 合并到上一帧（延长 end_ms / duration_seconds）；无可合并上一帧时兜底输出短 pause 帧，保证时间轴无“空洞”。
- `ai-pic-backend/tests/unit/test_dialogue_audio_service.py`：更新单测断言，验证短 pause 被合并后 end_ms 连续。
- `tasks.md`：补充并勾选“分镜占位合并短 pause beats”。

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_dialogue_audio_service.py`
- API 自测：
  - `POST /api/v1/scripts/17/storyboard/from-audio-timeline/generate-async`（`overwrite_existing=true`）触发重新生成
  - 轮询 `GET /api/v1/tasks/<id>` 至 completed
  - 通过 `GET /api/v1/episodes/10`（audio_timeline beats）与 `GET /api/v1/scripts/17/storyboard`（frames）对比，确认每个 scene 的 `sum(frame(end-start)) == (max(end)-min(start))`
- 浏览器（Selenium headless Chrome）：登录后打开 `http://localhost:8089/episodes/10/storyboard?scriptId=17`，确认时间轴区域与“来自时间轴”标识正常渲染。

## Next Steps

- 若需要进一步减少帧数，可在保持时长一致的前提下把“短 pause 合并策略”扩展为：合并到上一帧/下一帧/均分（可配置）。

## Linked Commits

- pending
