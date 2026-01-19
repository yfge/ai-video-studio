---
id: 2026-01-19T09-54-06Z-fix-script-regeneration-mock-fallback
date: 2026-01-19T09:54:06Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, scripts, deepseek, bugfix, prompts]
related_paths:
  - ai-pic-backend/app/services/ai/scripts_ai_manager.py
  - ai-pic-backend/app/prompts/templates/script_dialogues_short_drama.txt
  - ai-pic-backend/tests/unit/services/ai/test_scripts_ai_manager.py
summary: "Prevent script regeneration from falling back to mock_service when deepseek is selected"
---

## User Prompt
剧本内容不及格且选择 deepseek-chat 后仍落到 mock_service；要求按 provider 优化并做短剧全流程自测。

## Goals
- 解决“选择 deepseek-chat 但脚本 ai_model=mock_service”的回退问题，确保真实使用 deepseek 产出可用脚本。
- 降低剧本对白生成的提示词膨胀风险，避免 JSON 输出过长被截断导致解析失败。

## Changes
- `scripts_ai_manager`：
  - 当 `episode.scenes` 过多时强制重新规划场景（避免对白阶段输入/输出过大）。
  - 对 prompt 的 `episode` 做瘦身（只保留少量场景 sample + 总数），降低提示词体积。
- `script_dialogues_short_drama`：将每场对白建议条数下调到更可控范围，减少超长 JSON 输出。
- 单测：新增“episode scenes 过多时会触发 scene plan”的用例。

## Validation
- 后端单测：`cd ai-pic-backend && pytest tests/unit/services/ai/test_scripts_ai_manager.py -q`（通过）。
- Chrome E2E（脚本重生成，测试账号 `geyunfei`）：
  - 打开 `http://localhost:8089/episodes/1cca3cc61d7740b4b5f73bccf8fe4d32/workspace?tab=script&scriptId=101` → 点击“重新生成剧本”→ provider 选 `deepseek`、model 选 `deepseek-chat` → 提交，toast 返回 `task_id=642`。
  - MySQL 校验：`tasks.id=642` 最终 `COMPLETED`，`result_file_path=script:105`；`scripts.id=105` 的 `ai_model=ai_manager_deepseek`（不再是 `mock_service`）。

## Next Steps
- 让脚本/分场景 prompt 真正命中 `*_short_drama` 模板（目前 ai_manager 路径的 `story` payload 未携带 `story_format`）。
- 在短剧模板生效后，再跑一轮脚本重生成并人工检查“开场钩子/爽点落点/结尾卡点”。

## Linked Commits
- (this commit)
