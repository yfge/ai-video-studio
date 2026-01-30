---
id: 2026-01-19T10-09-00Z-enable-short-drama-script-prompts
date: 2026-01-19T10:09:00Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, scripts, prompts, short-drama]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
summary: "Propagate story_format into script payloads so short-drama prompt variants take effect"
---

## User Prompt

短剧故事/剧本模板要“每集都有爽点”，并做端到端验证；现有脚本质量不稳定。

## Goals

- 让脚本生成（script scenes/dialogues）在 `story_format=short_drama` 时实际命中 `*_short_drama` 提示词模板。
- 在生成结果中稳定出现：开场钩子、爽点落点、结尾卡点。

## Changes

- `scripts_legacy` 的 prompt payload 补齐 `story_format`：
  - `episode_data.story_format` 从 `episode.story.story_format` 透传。
  - `story_data.story_format` 从 `story.story_format` 透传。

## Validation

- 后端单测：`cd ai-pic-backend && pytest tests/unit/test_storyboard_image_task_image_gen_persistence.py -q`（通过）。
- Chrome E2E（短剧脚本重生成验证，测试账号 `geyunfei`）：
  - 在 `http://localhost:8089/episodes/1cca3cc61d7740b4b5f73bccf8fe4d32/workspace?tab=script&scriptId=105` 点击“重新生成剧本”→ provider 选 `deepseek`、model 选 `deepseek-chat` → 提交，toast 返回 `task_id=643`。
  - Celery 日志确认 prompt 已切换到短剧模板：
    - `LLM Prompt Preview: 你是一个专业的短剧场景规划师...`
    - `LLM Prompt Preview: 你是一个专业的短剧对白与舞台指示写手...`
  - MySQL 校验：`tasks.id=643` 完成后 `result_file_path=script:106`；`scripts.id=106` 的 `ai_model=ai_manager_deepseek`，并且 `scenes[0].summary`/`scenes[3].summary`/`scenes[last].summary` 分别包含 `开场钩子：`、`爽点：`、`卡点：`。

## Next Steps

- 针对 30 分钟短剧集数的场景数建议再做一版自适应（当前短剧场景模板默认 3-6 场景，可能偏少）。
- 继续全流程：IP → 环境 → 故事 → 剧本 → 分镜生图/生视频（Google Image 3.5 / Veo），每张图下载验收。

## Linked Commits

- (this commit)
