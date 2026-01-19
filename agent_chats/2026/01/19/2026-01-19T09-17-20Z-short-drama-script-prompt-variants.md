---
id: 2026-01-19T09-17-20Z-short-drama-script-prompt-variants
date: 2026-01-19T09:17:20Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, scripts, short-drama]
related_paths:
  - ai-pic-backend/app/prompts/template_resolver.py
  - ai-pic-backend/app/prompts/templates/script_scenes_short_drama.txt
  - ai-pic-backend/app/prompts/templates/script_scenes_short_drama.yaml
  - ai-pic-backend/app/prompts/templates/script_dialogues_short_drama.txt
  - ai-pic-backend/app/prompts/templates/script_dialogues_short_drama.yaml
  - ai-pic-backend/app/prompts/templates/system_prompt_story_short_drama.txt
  - ai-pic-backend/app/prompts/templates/system_prompt_story_short_drama.yaml
  - ai-pic-backend/app/prompts/templates/system_prompt_script_short_drama.txt
  - ai-pic-backend/app/prompts/templates/system_prompt_script_short_drama.yaml
  - ai-pic-backend/tests/unit/test_prompt_template_resolver_story_format_variants.py
summary: "Make script generation story_format-aware with short-drama scene + dialogue prompt variants"
---

## User Prompt
全局检查文生图/图生图提示词规范；按 provider 优化；并为短剧补齐“每集都有爽点”的故事/剧本模板，原子化提交并做全流程自测。

## Goals
- 让短剧的“分场景规划”和“对白生成”在 `story_format=short_drama` 时走专用模板。
- 在模板层明确约束：开场钩子 → 中段爽点落点 → 结尾卡点（留悬念/反转），避免“扯淡、不及格”的松散文本。

## Changes
- `template_resolver`：把 `script_dialogues` 纳入 story_format-aware 解析（允许自动选择 `*_short_drama` 变体）。
- 新增短剧模板：
  - `script_scenes_short_drama.*`：分集/分场景规划时强化冲突升级与爽点落点。
  - `script_dialogues_short_drama.*`：对白生成时强化“信息差、反击、揭露、卡点”的节奏。
  - `system_prompt_story_short_drama.*` / `system_prompt_script_short_drama.*`：短剧通用系统约束。
- 单测：新增 resolver 变体选择测试，保证 `story_format=short_drama` 会命中对应模板。

## Validation
- 后端单测：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（通过）。
- Chrome E2E（脚本重生成 smoke，测试账号 `geyunfei`）：
  - 进入 `http://localhost:8089/episodes/1cca3cc61d7740b4b5f73bccf8fe4d32/workspace?tab=script&scriptId=101` → 点击“重新生成剧本”→ 选择 `deepseek-chat` → 提交，任务返回 `task_id=641`。
  - 观察到脚本列表最新版本的 `ai_model` 出现 `mock_service`（与选择不一致），该问题在后续提交中排查修复。

## Next Steps
- 排查“选择 deepseek-chat 但落到 mock_service”的参数透传/任务处理问题，并在 Chrome 实测确认实际走 deepseek。
- 用短剧模板做一次端到端：生成第 1 集脚本 → 分镜 → Google Image 3.5 生图并下载验图 → Google Veo 生视频。

## Linked Commits
- (this commit)
