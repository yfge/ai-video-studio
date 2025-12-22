---
id: 2025-12-22T14-21-06Z-environment-model-params
date: 2025-12-22T14:21:06Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, backend, refactor, bugfix]
related_paths:
  - ai-pic-backend/app/services/providers/volcengine_provider/image.py
  - ai-pic-backend/app/services/providers/volcengine_provider/models.py
  - ai-pic-frontend/src/app/environments/[id]/page.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentDetailView.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentHeader.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentImagesPanel.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentSidePanel.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentVariantModal.tsx
  - ai-pic-frontend/src/components/features/environments/types.ts
summary: "Split environment detail UI and fix Volcengine Seedream 4.5 defaults"
---

## User Prompt
http://localhost:8089/environments/aab17f172446462a97e738772337d272 这个页面创建生成任务 还是不能选择模型设置参数；环境文生图任务使用火山 seedream 4.5 失败。

## Goals
- 让环境详情页支持选择模型与参数后创建生成任务。
- 修复 Volcengine Seedream 4.5 的模型标识与默认分辨率，避免生成失败。

## Changes
- 拆分环境详情页面为独立子组件，侧边栏加入可配置的模型参数输入区。
- 修复 Volcengine 模型类型推断逻辑，确保远端模型列表可用并替换 Seedream 4.5 模型 ID。
- 为 Seedream 4.5 默认分辨率设置为 2K，并补充 4K 尺寸映射。
- 环境生成表单加载模型时自动填入默认分辨率。

## Validation
- MCP Chrome: 登录 `geyunfei`，进入环境详情页，选择提供商“火山引擎”与模型“doubao-seedream-4-5”，分辨率自动为 2K，点击“创建生成任务”；跳转任务管理页并刷新后，新任务状态显示“已完成”。
- `npm run lint` (ai-pic-frontend) ✅
- `pytest` (ai-pic-backend) ❌ 91 failed, 13 errors (fixture 缺失/多项既有失败)。
- `./docker/build_prod_images.sh` ✅

## Next Steps
- 排查后端现有 pytest 大规模失败原因并修复基础 fixtures。
- 若需要，回到环境详情页刷新图片确认新图已落库。

## Linked Commits
- (pending)
