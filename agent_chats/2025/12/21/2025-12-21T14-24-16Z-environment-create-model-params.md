---
id: 2025-12-21T14-24-16Z-environment-create-model-params
date: 2025-12-21T14:24:16Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, environments, refactor]
related_paths:
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/components/features/index.ts
  - ai-pic-frontend/src/components/features/environments/EnvironmentCreateOverlay.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentList.tsx
  - ai-pic-frontend/src/components/features/environments/index.ts
  - ai-pic-frontend/src/components/features/environments/types.ts
summary: "Refactored environment creation UI and added model-parameterized reference image generation on create."
---

## User Prompt

- 环境参考图在第一次创建时就应该可以选择模型参数

## Goals

- 在创建环境资产时提供可选的模型参数配置以生成参考图
- 拆分环境页面组件，满足页面与组件体积限制

## Changes

- 拆分环境列表与创建表单为独立 feature 组件，并简化页面逻辑
- 在创建弹窗中新增参考图 AI 生成参数（模型/风格/数量/分辨率）并提交异步生成任务
- 新增环境创建表单的类型与共享导出

## Validation

- `npm run lint`
- `./docker/build_prod_images.sh` (首次 120s 超时，随后重跑完成)
- MCP Chrome: `http://localhost:3000/login` → `ERR_CONNECTION_REFUSED`
- Backend: `docker restart ai-video-backend` 后 `http://localhost:8000/health` 返回 200
- MCP Chrome: `http://localhost:8089/login` 登录 `geyunfei/Gyf@845261` → 环境资产 → 创建环境资产（启用生成并选择模型参数）→ 提示“创建成功，已提交参考图生成任务”
- MCP Chrome: `http://localhost:8089/tasks` 查看“环境文生图 - 环境aab17f172446462a97e738772337d272”任务失败，错误为 OSS 持久化阶段下载 OpenAI 图像 403（签名无效）

## Next Steps

- 如需确认生成结果，可进入新环境详情页刷新查看任务产出图
- 修复图像持久化 403 后重试环境参考图生成任务

## Linked Commits

- a3a7d01
