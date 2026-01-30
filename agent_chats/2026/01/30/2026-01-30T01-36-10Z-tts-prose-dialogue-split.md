---
id: 2026-01-30T01-36-10Z-tts-prose-dialogue-split
date: 2026-01-30T01:36:10Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, audio, fix]
related_paths:
  - ai-pic-backend/app/services/audio/dialogue_processing/prose_dialogue_splitter.py
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/tests/unit/services/audio/test_prose_dialogue_splitter.py
  - tasks.md
summary: "Split narration prose into per-speaker dialogue lines for TTS audio generation"
---

## User Prompt

对白音轨在后期变成了旁白描述（例：episode render `20260130/003919/58aa15ef.mp4`），需要在 docker 环境中验证并修复对白生成链路。

## Goals

- 修复“旁白 prose 混入多角色台词”导致的 TTS 旁白化问题，让对白音轨按角色发声。
- 保持 Story 角色注册表约束：只允许已注册角色 + 少量泛化角色（旁白/路人/店员）。
- 增加最小单测覆盖，避免回归。

## Changes

- 新增 prose 拆分器：从旁白段落中提取引号台词、推断 speaker，并跳过 UI/屏幕文本引用。
- 在 `generate_scene_dialogue_audio()` 中接入 repair：对白进入 TTS 前先做拆分；同时清洗 stage directions 中嵌入的引号对白，避免 action beat 过长。
- 新增单测覆盖拆分/跳过 UI 文本/旁白段落 repair。
- 更新 `tasks.md`：补充该 bugfix 的完成项，保持任务板可追踪。

## Validation

- 本地：
  - `cd ai-pic-backend && pytest -q tests/unit/services/audio/test_prose_dialogue_splitter.py`（3 passed）
- Docker（dev compose）：
  - 重启：`docker compose -f docker/docker-compose.dev.yml restart ai-video-backend ai-video-celery-worker ai-video-celery-beat`
  - 重跑对白音轨（overwrite）：
    - `POST /api/v1/scripts/117/dialogue-audio/generate-async` → task_id=5891（completed）
  - 重跑 episode 音频 + 时间轴（overwrite）：
    - `POST /api/v1/scripts/117/audio-timeline/generate-async` → task_id=5892（completed）
    - 新的 episode 音频（mp3）：`http://resource.lets-gpt.com/episode-dialogue/episodes/audio/20260130/022315/e9e08f40.mp3`
    - `episode_id=133` 的 `audio_timeline.beats`：68（dialogue=32 / action=14 / pause=22）
    - dialogue speaker 分布：老拐=16，文闻=12，旁白=4（不再出现“大段旁白朗读多角色对话”的情况）
  - 修正“自有音轨版”成片（替换音轨）：
    - 新的 tts_audio mp4：`http://resource.lets-gpt.com/ai-generated/episode-renders/video/20260130/022807/c7cc5ce7.mp4`
    - 已回写 `episode_id=133.extra_metadata.episode_renders.tts_audio` 的 `url/audio_url`

## Next Steps

- 在 script 生成阶段补充更严格的对白结构校验/repair（避免源头产生 prose 混入对白）。
- 为“覆盖音轨但不覆写 storyboard”提供更平滑的再生成路径（避免 pipeline 误触发 storyboard overwrite guard）。

## Linked Commits

- (pending)
