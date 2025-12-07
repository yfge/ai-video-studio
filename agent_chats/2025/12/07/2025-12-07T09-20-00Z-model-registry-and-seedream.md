---
id: 2025-12-07T09-20-00Z-model-registry-and-seedream
date: 2025-12-07T09:20:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, ai-models, image]
related_paths:
  - AGENTS.md
  - CLAUDE.md
  - GEMINI.md
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/core/config.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/base.py
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/components/SmartInputField.tsx
  - ai-pic-frontend/src/utils/api.ts
  - docs/TESTING_GUIDE.md
  - docs/api/
summary: "Unify model registry, add Google provider, improve Seedream img2img and virtual IP image flows, and update agent guidance/docs"
---

## User Prompt

- 让故事/图像生成页面的模型列表统一管理，支持按官方接口获取模型；修复虚拟 IP 图生图保存；补充测试指南等。

## Goals

- 统一模型列表接口，开放按 source 选择（remote/static/auto），并接入 OpenAI/Google/Volcengine 等。
- 完善 Seedream 图生图为真正 image-to-image；前端图生图保存为资产并支持数量/size 透传；虚拟 IP AI 助手传入用户已填内容。
- 更新 AGENTS 验证要求与测试指南；新增官方 API 文档存档。

## Changes

- AGENTS.md 及 CLAUDE/GEMINI 镜像：新增浏览器端到端验证要求，保持镜像一致。
- 模型注册中心：`ai_providers` 新增 `source` 参数，默认 static；`AIServiceManager.list_models` 汇总所有 Provider，OpenAI 支持 `/v1/models` 远端列表 + 白名单交集，BaseProvider 提供远端拉取默认实现；新增 GoogleProvider（Gemini 文本）；配置增加 GOOGLE_API_KEY/DEFAULT_MODEL。
- Volcengine Seedream：实现 `image_to_image`（Ark `/images/generations`，参考图转 data:image base64，支持多图组图参数）；声明支持 IMAGE_TO_IMAGE。
- 虚拟 IP 图像页：图生图调用 `/virtual-ips/{id}/images/{image_id}/variants` 入库，支持 count/size 透传，UI 成功后直接加到列表，不再新标签下载；文生图/图生图分辨率选项按模型白名单；图生图生成数量生效。
- SmartInputField：AI 助手 basic_info 汇总用户已填字段，提升上下文注入。
- API 类型同步：img2img payload 增加 size，生成/变体接口参数对齐。
- 文档：新增 `docs/TESTING_GUIDE.md`（虚拟 IP 图像/图生图验证指南），存档 OpenAI/Volcengine/Google 文档到 docs/api/。

## Validation

- 前端 lint：`npm --prefix ai-pic-frontend run lint` 通过。
- 手工：虚拟 IP 图像页 `http://localhost:8089/virtual-ip/1/images` 图生图生成多张变体，列表新增 variant 资产，无自动下载；故事生成页模型下拉渲染正常（仅 OpenAI 文本模型）。

## Next Steps

- 实现环境资产 CRUD 与场景/分镜绑定，分镜图像/视频生成链路注入环境与角色参考图。
- 在故事/分镜界面提供环境选择器及环境管理 UI。

## Linked Commits

- (pending)
