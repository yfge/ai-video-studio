---
id: 2026-01-19T06-40-54Z-storyboard-prompt-plan-fix
date: 2026-01-19T06:40:54Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, storyboard, prompts, fix]
related_paths:
  - ai-pic-backend/app/prompts/templates/fragments/image_macros.txt
  - ai-pic-backend/app/prompts/templates/storyboard_generation.txt
  - ai-pic-backend/app/prompts/templates/storyboard_generation.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_scene.txt
  - ai-pic-backend/app/prompts/templates/storyboard_scene.yaml
  - ai-pic-backend/app/services/ai/storyboard_plan.py
  - ai-pic-backend/tests/unit/test_image_prompt_templates.py
  - ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py
  - ai-pic-backend/tests/unit/services/ai/test_storyboard_plan_mixin.py
summary: "Harden storyboard prompts against readable text artifacts and stabilize plan parsing to avoid empty/placeholder frames."
---

## User Prompt
全流程测试短剧（deepseek 文生文、Google Image 3.5 生图、Google Veo 生视频）；发现分镜生成偶发空结果/占位文本，以及分镜图出现文字风险，要求修复并继续端到端验证。

## Goals
- 分镜结构生成稳定：避免 schema 不匹配导致的空分镜/占位分镜。
- 分镜图提示词语义更严格：明确“不要任何可读文字/中文字符/水印/字幕”，减少 UI/道具文字污染。
- 补齐单测，确保模板与解析行为可回归验证。

## Changes
- 强化图像提示词通用约束：补充“禁止任何可读文字/中文字符/标识/水印，标牌保持空白或模糊”要求（`ai-pic-backend/app/prompts/templates/fragments/image_macros.txt`）。
- 强化分镜场景提示词：禁止直接引用台词原句、禁止在描述里写“爽点/钩子”等标签、禁止可读屏幕/标识文字，并同步 bump 版本（`ai-pic-backend/app/prompts/templates/storyboard_scene.txt`, `ai-pic-backend/app/prompts/templates/storyboard_scene.yaml`）。
- 同步更新分镜生成模板版本（`ai-pic-backend/app/prompts/templates/storyboard_generation.txt`, `ai-pic-backend/app/prompts/templates/storyboard_generation.yaml`）。
- 修复分镜规划解析的根因：在 `StoryboardModel.model_validate()` 前对 LLM 输出做归一化，将 `ad_snippet` 字符串/`reference_images` 字符串自动纠正为 schema 期望结构，避免校验失败导致回退到占位分镜（`ai-pic-backend/app/services/ai/storyboard_plan.py`）。
- 新增/更新单测覆盖模板约束与字段纠正逻辑（`ai-pic-backend/tests/unit/test_image_prompt_templates.py`, `ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py`, `ai-pic-backend/tests/unit/services/ai/test_storyboard_plan_mixin.py`）。

## Validation
- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- API 手工回归：对 `script_id=103` 重新生成分镜结构与分镜图（deepseek + google gemini 3.5），下载 15 张分镜图并人工检查：无可读中文/水印/字幕。
- Chrome（MCP）回归：登录 `geyunfei` → 打开故事详情 → 进入第 1 集工作台 → 分镜 Tab，确认 15 帧均有图像且无占位文本。

## Next Steps
- 修复 Google Veo 视频生成链路（需要异步任务 `task_id` + 轮询状态），并继续分镜视频端到端测试与下载验收。

## Linked Commits
- (pending)

