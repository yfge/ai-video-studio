---
id: 2026-01-09T11-36-07Z-virtual-ip-runtime-prompt-template
date: "2026-01-09T11:36:07Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image, prompts]
related_paths:
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/app/prompts/templates/virtual_ip_image.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_image.yaml
  - docs/design/image-generation-unification.md
summary: "Use PromptManager runtime template for Virtual IP text-to-image prompts (improves quality consistency and unifies prompt management)"
---

## User Prompt

用户追问「为什么没有用统一的提示词管理？」，并要求对虚拟 IP / 环境 / 分镜的图像生成链路进行统一梳理（优先提升图像生成质量与一致性）。

## Goals

- 为虚拟 IP 文生图引入“运行时 prompt 模板”（直接喂给图像模型），避免继续使用散落的字符串拼接。
- 在设计文档中补齐 PromptManager 在图像生成中的统一策略（区分 runtime prompt vs prompt-generator）。

## Changes

- 新增 PromptManager 模板 `virtual_ip_image`（运行时模板，直接输出图像模型 prompt）：
  - `ai-pic-backend/app/prompts/templates/virtual_ip_image.txt`
  - `ai-pic-backend/app/prompts/templates/virtual_ip_image.yaml`
- 虚拟 IP 文生图改为优先使用 `virtual_ip_image` 渲染结果作为最终 prompt，并保留渲染失败时的兼容 fallback：
  - `ai-pic-backend/app/services/ai/images_generation.py`
- 更新图像生成统一化设计文档，补齐“统一提示词管理（PromptManager）”策略与当前落地进度说明：
  - `docs/design/image-generation-unification.md`

## Validation

- Chrome E2E（Docker dev + Nginx，`http://localhost:8089`）：
  1. 登录：`geyunfei` / `Gyf@845261`
  2. 进入虚拟 IP 列表：`/virtual-ip`，打开角色「老拐」详情：`/virtual-ip/233525e9045146d580a1d18ef4a28161#ip-images`
  3. 点击「AI 生成图片」并选择提供商/模型：`volcengine:doubao-seedream-4-5-251128`（Seedream 4.5）
  4. 点击「提交生成任务」→ 跳转到 `/tasks`，确认创建任务成功：`虚拟IP文生图 - 老拐`（Task ID: 542）并能在「详情」中看到参数 `model=size/count/style` 等字段
  5. 任务当时仍为「生成中」（用于验证链路可提交且无前端/后端运行时错误）

## Next Steps

- 评估是否需要引入可选的“prompt-rewrite pipeline”（LLM 生成 `positive_prompt/negative_prompt`，并将 `negative_prompt` 映射到支持的 provider）。
- Phase 4：分镜图生图接入归一化层，并补齐 Chrome E2E 验证记录。

## Linked Commits

- TBD
