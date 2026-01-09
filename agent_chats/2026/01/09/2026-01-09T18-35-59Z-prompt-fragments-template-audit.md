---
id: 2026-01-09T18-35-59Z-prompt-fragments-template-audit
date: "2026-01-09T18:35:59Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, image-gen, quality-consistency]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation_helpers.py
  - ai-pic-backend/app/prompts/template_audit.py
  - ai-pic-backend/app/prompts/templates/environment_image.txt
  - ai-pic-backend/app/prompts/templates/fragments/image_macros.txt
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_image.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_image_variant.txt
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/app/services/story_structure/environment_image_requests.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_generation.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_service.py
  - ai-pic-backend/app/services/virtual_ip/virtual_ip_image_prompts.py
  - ai-pic-backend/tests/unit/test_image_prompt_templates.py
  - docs/design/image-generation-unification.md
summary: "Unify image-generation prompt constraints via shared fragments and add template audit (name/version/hash) into tasks and metadata."
---

## User Prompt

继续 Phase 2，并回答「为什么没有用统一的提示词管理？」——要求把虚拟 IP / 环境 / 分镜 的图像生成提示词进行统一梳理，进一步提升质量一致性。

## Goals

- 抽取提示词中的通用约束/负面词/质量片段为可复用 fragments，避免多模板重复导致漂移。
- 在 Task.parameters 与落库元数据中记录 prompt 模板的 name/version/hash，提升可追溯性与可回放性。

## Changes

- 新增 `app/prompts/templates/fragments/image_macros.txt`，集中管理通用质量与约束片段（no text/no watermark/no collage 等）。
- 更新 runtime prompt 模板：
  - `virtual_ip_image` / `virtual_ip_image_variant`：改为引用 fragments，保持输出语义一致。
  - `environment_image`：追加通用 no-text 约束，减少环境图出现标牌/字幕等不稳定因素。
  - `storyboard_image_prompt`：引用 fragments 中的 collage 约束短语，避免模板漂移。
- 新增 `app/prompts/template_audit.py`：计算模板指纹（template/resolved/version/sources_hash）并提供 `sha256_text`。
- 将 `prompt_template` 注入到任务 payload 与落库元数据：
  - Virtual IP 文生图：payload + generation_params + metadata
  - Virtual IP 图生图：payload + generation_params + metadata + image_gen meta
  - Environment：payload + env.extra_metadata（记录 prompt_sha256）
  - Storyboard：image_gen meta 追加 prompt_template/prompt_sha256

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_image_prompt_templates.py -q`
- `pre-commit run`
- `./docker/build_prod_images.sh`（tag: `fbd5443`）
- Chrome E2E（http://localhost:8089）：
  - 登录 `geyunfei`
  - 打开虚拟 IP「老拐」图片管理页 → `AI 生成图片` → `提交生成任务`
  - 在 `/tasks` 打开任务详情，确认 Task ID=547 的 parameters 内包含 `prompt_template`（含 version 与 sources_hash）
  - 备注：点击「开始」返回“任务状态不允许开始执行”（疑似现有任务状态机/执行入口限制）

## Next Steps

- 提交本次原子改动（包含本条 agent_chats 记录）。
- 进一步把 UI 的模型选择默认值收敛到“质量一致性优先”的配置（避免落到 `google:gemini-2.0-flash-exp` 这种不适用于图像的模型字符串）。

## Linked Commits

- (pending) refactor(backend): unify prompt fragments and audit
