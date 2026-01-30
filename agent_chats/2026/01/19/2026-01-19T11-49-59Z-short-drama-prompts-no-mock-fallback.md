---
id: 2026-01-19T11-49-59Z-short-drama-prompts-no-mock-fallback
date: 2026-01-19T11:49:59Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, short-drama]
related_paths:
  - ai-pic-backend/app/prompts/templates/episode_generation_short_drama.txt
  - ai-pic-backend/app/prompts/templates/script_dialogues_short_drama.txt
  - ai-pic-backend/app/prompts/templates/script_scenes_short_drama.txt
  - ai-pic-backend/app/services/ai/episodes.py
  - ai-pic-backend/app/services/ai/scripts.py
  - ai-pic-backend/app/services/ai/story_outline.py
summary: "Strengthened short-drama prompts (payoff/conflicts) and disabled mock fallback when a model/provider is explicitly pinned."
---

## User Prompt

全局检查文生图/图生图提示词规范与 provider 参数一致性；并补齐短剧故事/剧本模板（每集都有爽点），要求生文用 deepseek-chat，避免生成内容“扯淡/不及格”。

## Goals

- 短剧分集与剧本生成更明确地落地“爽点=收获点”，并且 Episode plan 必须包含可持久化的冲突结构。
- 当用户显式指定 provider/model（如 deepseek-chat）时，生成失败应当直接报错而不是静默回退到 mock，避免垃圾内容落库。

## Changes

- 更新 `ai-pic-backend/app/prompts/templates/episode_generation_short_drama.txt`：补齐 `conflicts`/`character_arcs`/`payoff` 等硬性要求，并强化“卡点”场景输出示例。
- 更新 `ai-pic-backend/app/prompts/templates/script_scenes_short_drama.txt` 与 `ai-pic-backend/app/prompts/templates/script_dialogues_short_drama.txt`：将“爽点”明确为“主角获得具体收益”，避免抽象情绪爽点。
- 更新 `ai-pic-backend/app/services/ai/story_outline.py` / `ai-pic-backend/app/services/ai/episodes.py` / `ai-pic-backend/app/services/ai/scripts.py`：当 `prefer_provider` 或 `model` 被显式指定时，禁用 legacy/mock 回退并返回 `None`（由上层转换为可见错误）；同时补充日志便于排查。

## Validation

- `docker exec ai-video-backend bash -lc "cd /app/ai-pic-backend && pytest tests/unit tests/services tests/scripts"`
- `./docker/build_prod_images.sh`

## Next Steps

- Chrome 端到端跑短剧全链路（IP→环境→故事→剧集→剧本→分镜图→分镜视频），并逐张下载抽检图片质量；若出现“乱图/拼接/跑题/人物不一致”，回到提示词与参数归一化继续修正。
- 更新 `tasks.md`：补齐本次改动对应的完成项，并拆分后续 “deepseek-chat 指令优化” 与 “E2E 抽检” 任务。

## Linked Commits

- (pending)
