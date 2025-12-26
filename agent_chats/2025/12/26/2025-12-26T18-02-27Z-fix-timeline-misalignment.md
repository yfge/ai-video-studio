---
id: 2025-12-26T18-02-27Z-fix-timeline-misalignment
date: "2025-12-26T18:02:27Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, timeline, audio, bugfix]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/prompts/templates/script_scenes.txt
  - ai-pic-backend/app/services/timeline_agent/agent.py
summary: "Fix episode timeline misalignment by defaulting to latest script and avoiding impossible Timeline Agent repair loops when dialogue is sparse."
---

## User Prompt

现在从剧本，到对白，到分镜这个过程时间轴还是对不齐（对白过少，音频过短），希望整体解决；并用现有 MySQL 数据和 Chrome 回归验证 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script`。

## Goals

- 避免工作台默认选到旧剧本版本导致“对白音轨过短/时间轴不齐”的错觉。
- 在对白稀疏时，仍能稳定生成与剧集目标时长对齐的 scene 音轨与 episode 时间轴。
- 用给定 episode 的真实数据做一次端到端回归验证。

## Changes

- `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`：`/scripts/episode/*` 列表在 Python 侧按 `id` 倒序排序，确保前端默认选最新剧本；并增强 `_populate_dialogues_and_stage_if_missing` 为“按场景补齐缺失对白/舞台指示”，避免空内容阻断后续音轨/时间轴生成。
- `ai-pic-backend/app/services/timeline_agent/agent.py`：当提供 `target_duration_seconds` 时，不再把 `duration_too_short` 作为硬错误（补足由音频 segment padding 负责），避免触发不可满足的修复循环与无谓的 LLM 重试。
- `ai-pic-backend/app/prompts/templates/script_scenes.txt`：补充对白占比的“节奏硬约束”，减少连续低对白场景带来的下游时长/节奏风险。

## Validation

- Chrome（episode=46 / business_id=cd378417b7f143eab5bc6d063cd7f6e7）：
  - 打开 `.../workspace?tab=script` 默认选中最新 `v1.7 (script_id=51)`。
  - 生成时间轴后页面显示：scene 音轨 `4/4` 已生成（≈30s/15s/15s/120s），episode 时间轴 beats=37，episode 音频总时长=180s，并可直接播放 OSS mp3。
- MySQL 校验：
  - `episodes.extra_metadata.audio_timeline.script_id = 51` 且 `duration_seconds = 180.0`。
  - `scenes.metadata.dialogue_audio.duration_seconds` 与 `estimated_duration_seconds` 对齐（30/15/15/120）。
- `./docker/build_prod_images.sh` 构建并推送成功。
- `pytest`：本地直接运行 `pytest` 存在大量与本变更无关的既有失败（外部依赖/用例假设等），未作为本次回归的判定依据。

## Next Steps

- 将 Timeline Agent 的默认 provider/model 固化到可用项（避免 auto 模式偶发选到无权限模型导致噪声重试）。
- 如果需要提升“对白过少”的内容质量：在剧本生成阶段增加“按场景对白最低阈值/补写”链路（与时长预算联动），而不是仅依赖下游 padding。

## Linked Commits

- (pending)
