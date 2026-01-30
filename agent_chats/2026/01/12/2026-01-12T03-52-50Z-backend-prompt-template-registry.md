---
id: 2026-01-12T03-52-50Z-backend-prompt-template-registry
date: "2026-01-12T03:52:50Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, image-gen, quality-consistency]
related_paths:
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/app/services/story_structure/environment_image_requests.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_generation.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_requests.py
  - ai-pic-backend/app/services/virtual_ip/virtual_ip_image_prompts.py
summary: "Register Virtual IP image prompt templates in PromptTemplate enum for unified prompt management"
---

## User Prompt

- 为什么没有用统一的提示词管理？继续提升“质量一致性”。
- 先做后端，把虚拟 IP / 环境 / 分镜的提示词体系梳理得更一致。

## Goals

- 将虚拟 IP 图像相关提示词模板纳入统一 `PromptTemplate` 注册表，便于：
  - API 枚举输出一致（前端可统一展示/选择/追溯）
  - 审计字段 `prompt_template/prompt_sha256` 的来源稳定可控
- 让图像生成相关代码尽量通过统一枚举引用模板名，减少硬编码字符串散落。

## Changes

- Prompt registry：
  - 在 `PromptTemplate` 中新增 `virtual_ip_image` 与 `virtual_ip_image_variant` 两个模板枚举，并补齐分类映射。
- Image prompt usage：
  - 将环境/分镜/虚拟 IP 图像链路的 `build_prompt_template_audit(...)` 参数从裸字符串切换为 `PromptTemplate.*.value`，降低模板名漂移风险。
  - 虚拟 IP 图像 prompt 渲染使用 `PromptTemplate.VIRTUAL_IP_IMAGE` / `PromptTemplate.VIRTUAL_IP_IMAGE_VARIANT`，与 prompts API 的枚举输出对齐。

## Validation

- 后端测试：
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome 端到端（提示词注册表核验）：
  - 登录 `http://localhost:8089/login`（geyunfei）。
  - DevTools 请求 `GET http://localhost:8000/api/v1/prompts/enums/templates`，确认返回中包含 `virtual_ip_image` 与 `virtual_ip_image_variant`。

## Next Steps

- 前端：将图像生成相关页面/弹窗的提示词模板信息与 `prompt_sha256` 做“可追溯展示”，并和 `generation_profile` 一起呈现。
- 后端：继续推进按 provider+model 的 profile 默认值覆盖（steps/cfg/negative 等），并补齐到所有图像域的 normalize。

## Linked Commits

- (pending)
