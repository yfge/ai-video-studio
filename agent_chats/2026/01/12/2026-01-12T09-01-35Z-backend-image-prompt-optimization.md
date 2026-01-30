---
id: 2026-01-12T09-01-35Z-backend-image-prompt-optimization
date: 2026-01-12T09:01:35Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, image-gen, quality]
related_paths:
  - ai-pic-backend/app/prompts/templates/fragments/image_macros.txt
  - ai-pic-backend/app/prompts/templates/environment_image.txt
  - ai-pic-backend/app/prompts/templates/environment_image.yaml
  - ai-pic-backend/app/prompts/templates/virtual_ip_image.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_image.yaml
  - ai-pic-backend/app/prompts/templates/virtual_ip_image_variant.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_image_variant.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.txt
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.yaml
summary: "Improve image-generation prompt templates for consistent quality across Virtual IP / Environment / Storyboard."
---

## User Prompt

- 整体优化生图相关的提示词，覆盖虚拟 IP（文生图/图生图）、环境（文生图/图生图）、分镜（图生图）并进行统一梳理。

## Goals

- 提升不同生图入口的“质量一致性”（质量关键词、负向约束、结构化输出）。
- 减少常见坏例：水印/字幕/文字、拼接/分屏、UI/边框、低清/噪点等。
- 环境图强调“只生成环境，不要人物/角色/动物”，减少跑偏。
- 保持现有单测断言的关键约束（例如 storyboard 不包含 `no multiple faces`）。

## Changes

- `image_macros.txt`：增强 `quality_high(style, subject)`（区分动漫/写实、角色/场景），新增 `quality_storyboard()`；新增/强化环境与低质量相关 constraints。
- `environment_image.txt`：增加“只生成环境”的硬约束；统一追加低质量负向；Quality 使用 `subject="scene"`；`environment_image.yaml` 版本更新到 `1.3`。
- `virtual_ip_image.txt`：结构化拆行，Quality 使用 `subject="character"`；追加低质量负向；`virtual_ip_image.yaml` 版本更新到 `1.2`。
- `virtual_ip_image_variant.txt`：强调“只改 variant 指令、保持身份/发型/服装一致”；追加低质量负向；`virtual_ip_image_variant.yaml` 版本更新到 `1.3`。
- `storyboard_image_prompt.txt`：Quality 追加 `quality_storyboard()`；追加低质量负向与“参考图优先匹配一致性”说明；`storyboard_image_prompt.yaml` 版本更新到 `1.5`。

## Validation

- Unit tests
  - `cd ai-pic-backend && pytest tests/unit/test_image_prompt_templates.py -q`
  - `cd ai-pic-backend && pytest tests/unit/services/virtual_ip/test_virtual_ip_image_prompts.py -q`
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（pre-commit gate）
- Docker prod build
  - `./docker/build_prod_images.sh` ✅
- Chrome E2E (geyunfei / Gyf@845261)
  - 环境文生图：环境详情页 `模型参数测试环境` 点击“创建生成任务” → 任务页查看 `task_id=574`，`prompt_template.environment_image.version == 1.3`。
  - 虚拟IP文生图：虚拟IP `老拐` 图片管理点击 “AI 生成图片” 并提交 → 任务页查看 `task_id=575`，`prompt_template.virtual_ip_image.version == 1.2`。
  - 虚拟IP图生图：虚拟IP 图片条目点“图生图”并提交 → 任务页查看 `task_id=576`，`prompt_template.virtual_ip_image_variant.version == 1.3`。
- Notes
  - `cd ai-pic-backend && pytest`（全量）当前存在大量既有失败（86 failed / 7 errors）；本次以 pre-commit quick gate 为准，未新增相关失败。

## Next Steps

- 修复 `环境图像持久化失败 / 'dict' object has no attribute 'startswith'`（影响环境/虚拟IP 图生图链路）。
- 继续推进“生成参数 preset/profile” 与提示词 preset 的统一管理（provider+model 默认 steps/cfg/negative）。
- 考虑为“分镜图像生成任务”也补齐 `prompt_template` 参数审计字段，便于线上排查一致性问题。

## Linked Commits

- (pending)
