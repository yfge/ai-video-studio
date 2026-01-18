---
id: 2026-01-18T23-32-08Z-short-drama-prompts-fullflow
date: 2026-01-18T23:32:08Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, short_drama, e2e, image, video]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
  - ai-pic-backend/app/prompts/template_resolver.py
  - ai-pic-backend/app/prompts/templates/story_outline_short_drama.txt
  - ai-pic-backend/app/prompts/templates/story_outline_short_drama.yaml
  - ai-pic-backend/app/prompts/templates/episode_generation_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_short_drama.yaml
  - ai-pic-backend/app/prompts/templates/episode_from_outline_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline_short_drama.yaml
  - ai-pic-backend/app/prompts/templates/episode_duration_reject_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_duration_reject_short_drama.yaml
  - ai-pic-backend/app/prompts/templates/script_generation_short_drama.txt
  - ai-pic-backend/app/prompts/templates/script_generation_short_drama.yaml
  - ai-pic-backend/tests/unit/test_story_format_prompt_templates.py
  - tasks.md
summary: "Added short_drama prompt variants and verified end-to-end generation with DeepSeek text and Google image/video."
---

## User Prompt

全局检查并优化文生图/图生图提示词规范；新增短剧故事模板和剧本模板，要求每一集都有爽点；全流程测试：生文用 deepseek-chat，生图用 Google image 3.5 preview，生视频用 Google；原子化提交并更新 tasks.md。

## Goals

- 增加 `short_drama` 专用提示词模板，并确保真实生成链路会选中
- 让 Episode/Script 生成具备“每集必有爽点 + 结尾卡点”的硬性约束
- 完成一次端到端验证：DeepSeek 文生文（剧集+剧本）、Google 文生图、Google 文生视频

## Changes

- 扩展 prompt template resolver：支持 `short_drama`，并对 `episode_from_outline`/`episode_duration_reject`/`script_generation` 等模板启用 format-aware 分流
- 补齐 episode async 生成上下文：在 `story_data` 中传递 `story_format`，让 Episode Agent 能正确挑选 short_drama 模板
- 新增 short_drama 提示词模板（story/episode/script），显式注入“爽点/卡点”硬性规则，并要求至少 1 个场景 summary 以“爽点：”开头、最后 1 个以“卡点：”开头
- 新增单测覆盖 short_drama 模板可解析与关键断言；更新 `tasks.md` 对应任务状态

## Validation

- Backend tests: `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（789 passed）
- Chrome E2E（登录 `geyunfei`）：打开 `http://localhost:8089/episodes/4b2cf4f5322a4106b5b5994ba98b4e52/workspace?tab=overview&scriptId=102`，验证第 1 集“剧情要点”包含 `爽点：` 与 `卡点：`，且当前剧本为 `v1.0 (Script ID: 102)`，模型 `deepseek-chat`
- API E2E（关键任务与结果）：
  - Episode async（DeepSeek）：task `623` → `episodes:111`（story `20`《大冒险》），scene summaries 含 `爽点：`（场景 4）与 `卡点：`（场景 5）
  - Script async（DeepSeek）：task `624` → `script:102`（episode `111`），script scenes 保留 `爽点：`（scene 4）与 `卡点：`（scene 5）
  - Virtual IP 图像 async（Google image preview）：task `625` → `virtual_ip_image:1:84`（model `gemini-3-pro-image-preview`）
  - 视频生成（Google Veo 文生视频）：`POST /api/v1/ai/generate/video`（model `google:veo-3.1-fast-generate-preview`）返回 `video_url`
- Notes:
  - `POST /api/v1/ai/generate/video` 使用 `image_url + google:veo-3.1-generate-preview` 时，proxy 返回 `400 Bad Request`；当前 endpoint 会把该 `400` 包装成 `500`（需要单独修复错误透传以便调试）

## Next Steps

- 修复 `/api/v1/ai/generate/video` 的错误透传（HTTPException 不应被统一包装成 500），并排查 Veo image-to-video 的 400 参数约束
- 将“按 provider 动态加载参数解释/约束”的 UI 与 prompt 模板规范化继续推进（按 provider domain 逐步收敛）

## Linked Commits

- (this commit)
