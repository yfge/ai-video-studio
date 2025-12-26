---
id: 2025-12-26T15-18-01Z-audio-timeline-duration-padding
date: "2025-12-26T15:18:01Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, audio, timeline, refactor]
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/audio/dialogue_processor.py
  - ai-pic-backend/app/services/audio/dialogue_processing/__init__.py
  - ai-pic-backend/app/services/audio/dialogue_processing/text_utils.py
  - ai-pic-backend/app/services/audio/dialogue_processing/scene_extractors.py
  - ai-pic-backend/app/services/audio/dialogue_processing/segment_models.py
  - ai-pic-backend/app/services/audio/dialogue_processing/segment_padding.py
  - ai-pic-backend/app/services/audio/dialogue_processing/segment_builder.py
  - ai-pic-backend/app/services/audio/dialogue_processing/segment_intelligent_planner.py
  - ai-pic-backend/tests/unit/services/audio/test_dialogue_segment_padding.py
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
summary: "Align scene/episode audio durations to script targets via segment padding + WAV normalization"
---

## User Prompt
现在从剧本到对白到分镜的时间轴对不齐（对白过少、音频过短），希望从整体上解决；并用现有 Docker/MySQL 数据与 Chrome 回归验证：`/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script`。

## Goals
- 让场景级/剧集级音频时长与剧本规划时长一致，避免时间轴与分镜占位错位。
- 在对白内容不足时提供确定性的兜底补时策略，保证 pipeline 可收敛。
- 用真实回归数据（Episode 46 / Script 45）在 MySQL 与 Chrome 中验证修复生效。

## Changes
- [refactor] 将 `dialogue_processor.py` 拆分为 `app/services/audio/dialogue_processing/*` 小模块，并保留 `dialogue_processor.py` 作为兼容 facade。
- 增加分段补时兜底：当传入 `target_duration_seconds` 时，优先扩展 `action`/`pause` 段，并在不足时追加转场留白段，使 beats 总时长达到目标。
- 修复“补时 beats 正确但音频仍偏短”的问题：对白 TTS WAV（默认 32kHz）与静音 WAV（24kHz）混拼会导致 concat 后时长偏短；新增 `_normalize_wav(...)` 将 TTS 产物统一重采样到 24kHz mono PCM 后再拼接。
- 增加单元测试覆盖补时逻辑：`test_dialogue_segment_padding.py`。
- 修复 `episodes/[id]/page.tsx` 传参不匹配导致的 Next.js 生产构建失败（移除 `AudioTimelineSection` 未定义的 props）。

## Validation
- 单测：`cd ai-pic-backend && pytest tests/unit/services/audio/test_dialogue_segment_padding.py -q`
- 前端 lint：`cd ai-pic-frontend && npm run lint`
- 生产镜像构建（本地 buildx，不推送）：`docker buildx build --platform linux/amd64 -f docker/Dockerfile.backend.prod ...` 与 `docker buildx build --platform linux/amd64 -f docker/Dockerfile.frontend.prod ...`
- 回归数据重跑（容器内执行 Python snippet）：
  - 对 Episode `46` / Script `45` 重跑 `generate_scene_dialogue_audio(... target_duration_seconds=scene.estimated_duration_seconds, use_intelligent_timing=False)` → `generate_episode_audio_timeline` → `generate_storyboard_from_episode_audio_timeline`
  - MySQL 校验：`scenes.metadata.dialogue_audio.duration_seconds` 变为 `30/15/20/115`，`episodes.extra_metadata.audio_timeline.episode_audio.duration_seconds` 为 `180`
  - ffprobe 校验：episode mp3 实际时长约 `180s`
- Chrome (MCP)：登录 `geyunfei`，打开 `.../workspace?tab=timeline&scriptId=45`，页面展示“场景 1/2/3/4 时长=30/15/20/115 秒”，时间轴末尾到 `03:00`，剧集音频链接更新为 `.../episode-dialogue/episodes/.../150119/9f4413d8.mp3`。

## Next Steps
- 在剧本生成阶段强化“对白密度/字数预算”REACT（已有 `script_agent.py` 与 duration_orchestrator），让时长主要通过对白内容达标，补时只做兜底。
- 在 scene.metadata.dialogue_audio 中持久化 `target_duration_seconds` 以便线上排查（目前仅日志里可见）。

## Linked Commits
- fix(backend): align scene audio with duration targets
