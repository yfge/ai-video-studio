---
id: 2026-01-18T19-56-08Z-environment-img2img-prompt-template
date: 2026-01-18T19:56:08Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, prompts]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_variants.py
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/prompts/templates/environment_image_variant.txt
  - ai-pic-backend/app/prompts/templates/environment_image_variant.yaml
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/app/services/story_structure/environment_image_prompts.py
  - ai-pic-backend/app/services/story_structure/environment_image_requests.py
  - ai-pic-backend/tests/unit/test_image_prompt_templates.py
  - tasks.md
summary: "环境图生图变体改用独立提示词模板，并在任务审计中显式记录"
---

## User Prompt
全局检查文生图/图生图提示词规范，并根据 provider/domain 优化；环境图生图提示词需要更符合“在参考图基础上做局部变体”的语义。

## Goals
- 环境图生图（img2img variants）提示词语义清晰：保留空间布局/镜头视角，只按变体指令修改。
- 任务审计（task parameters / prompt_template）能区分文生图与图生图模板，便于排查 provider 行为差异。
- 维持兼容：PromptManager 渲染失败时有合理降级串联文本。

## Changes
- 新增 `environment_image_variant` 提示词模板（支持 `Base Prompt` + `Variant Instructions` 结构，内置一致性约束）。
- 新增 `compose_environment_variant_prompt()` 并让环境图生图变体生成链路统一使用该模板：
  - 同步影响：变体生成服务、异步 Task.prompt、Task.parameters.prompt_template 审计字段。
- 补单测覆盖 `environment_image_variant` 的渲染与关键约束字段。
- 更新 `tasks.md` 记录该项完成。

## Validation
- Backend unit test: `cd ai-pic-backend && pytest tests/unit/test_image_prompt_templates.py -q`
- Docker build: `./docker/build_prod_images.sh`
- Chrome E2E（提示词链路验证）：
  - 登录 `geyunfei`
  - 打开环境详情页 → 选择“图生图” → 输入变体指令（如“改为夜景，雨天，霓虹灯反射”）→ 提交
  - 在 `http://localhost:8089/tasks` 顶部任务中确认 prompt/parameters 内出现 `ENVIRONMENT_IMAGE_VARIANT` 与 `Variant Instructions:`（任务执行可能因 provider/配额失败，但提示词拼装与审计字段已验证）。
- 备注：尝试全量 `pytest` 在当前环境出现大量历史失败/fixture 不齐（与本改动无直接关联），因此以新增单测+端到端链路验证为主。

## Next Steps
- 对其他 img2img 场景（如分镜/虚拟 IP 变体）补齐“基准提示词 + 变体指令”的模板审计一致性。
- 继续梳理各 provider 的参数/能力差异，将 UI 元数据按 domain 透传并动态渲染表单提示。

## Linked Commits
- feat(backend): add environment img2img prompt template

