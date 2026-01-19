---
id: 2026-01-19T14-43-13Z-backend-story-pacing-template-input
date: 2026-01-19T14:43:13Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, short-drama]
related_paths:
  - ai-pic-backend/app/schemas/generation_requests.py
  - ai-pic-backend/app/services/ai/story_outline.py
  - ai-pic-backend/app/services/story_agent.py
  - ai-pic-backend/app/services/story/story_generation_prompt_preview.py
  - ai-pic-backend/app/services/story/story_generation_service.py
  - ai-pic-backend/app/prompts/templates/story_outline_short_drama.txt
summary: "Allow story generation to consume pacing template (hook_plan/twists/cliffhangers/ad_snippets) and inject into short-drama story outline prompt."
---

## User Prompt

全局检查文生图/图生图提示词规范；优化所有 provider 和域；按 provider 动态加载输入；原子化提交；并完成短剧全流程测试（deepseek-chat 文生文，google image 3.5 preview 文生图，google veo 文生视频）。在此提交中先补齐短剧故事模板/节奏模板输入，使故事生成阶段可接收并注入 hook_plan 等字段。

## Goals

- 让“市场/微类型/节奏模板”在故事生成阶段生效（不再被后端 schema 忽略）。
- 将预设 hook_plan / twist_density / cliffhanger_plan / ad_snippets 注入短剧故事概要提示词，提升 deepseek-chat 的结构化输出稳定性与爽点一致性。
- 为后续 E2E（IP→环境→故事→剧集→剧本→分镜）提供可追溯的参数落库。

## Changes

- 扩展 `StoryGenerationRequest`：新增 `pacing_template/hook_plan/twist_density/cliffhanger_plan/ad_snippets` 字段，并补齐 `EpisodeGenerationRequest/ScriptGenerationRequest` 的 `pacing_template`（与前端类型对齐）。
- 更新故事概要生成链路：将上述字段透传到 `ai_service.generate_story_outline`，并写入 `generation_params/extra_metadata`。
- 更新短剧故事概要提示词 `story_outline_short_drama.txt`：当提供节奏/投流预设时，以“优先遵守”的约束形式注入提示词。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`

## Next Steps

- 继续短剧全流程 E2E：环境图→故事/剧集/剧本→分镜图→分镜视频；逐张下载抽检并记录到 agent_chats。
- 若 deepseek-chat 输出仍不稳定：针对 story/script prompts 做进一步 deepseek 指令优化（严格 JSON/字段长度/爽点密度）。

## Linked Commits

- (pending) `feat(backend): accept short-drama pacing template inputs`
