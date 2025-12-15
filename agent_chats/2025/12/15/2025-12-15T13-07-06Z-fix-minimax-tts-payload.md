---
id: 2025-12-15T13-07-06Z-fix-minimax-tts-payload
date: 2025-12-15T13:07:06Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tts, minimax]
related_paths:
  - ai-pic-backend/app/services/providers/minimax_provider.py
  - ai-pic-backend/tests/unit/test_minimax_provider_tts_payload.py
summary: "Fix MiniMax TTS payload type/field issues to unblock dialogue audio generation"
---

## User Prompt

对白音轨任务在实际跑 celery 时失败，错误为「所有语音合成提供商都失败了」，需要排查并修复使其可生成音频并上传 OSS。

## Goals

- 修复 MiniMax TTS 请求体中的字段与类型问题（避免 invalid params）
- 让对白音轨生成任务能在真实环境中成功执行，继续后续 timeline / storyboard 生成与 E2E 验证

## Changes

- `ai-pic-backend/app/services/providers/minimax_provider.py`：
  - 过滤 `voice_type`（ai_service_manager 会透传，但 MiniMax `/t2a_v2` 不接收）
  - 将 `pitch/sample_rate/bitrate/channel` 统一转换为 int，避免 float 导致类型不匹配
  - `emotion` 默认改为可选（不传则不写入请求体）
- `ai-pic-backend/tests/unit/test_minimax_provider_tts_payload.py`：新增单测校验 payload 的 pitch 类型与 voice_type 过滤

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`

## Next Steps

- 重启 celery worker（加载新 provider 代码）后重跑对白音轨 → 时间轴 → 分镜占位链路，并记录 OSS URL/frames 数量

## Linked Commits

- (pending)
