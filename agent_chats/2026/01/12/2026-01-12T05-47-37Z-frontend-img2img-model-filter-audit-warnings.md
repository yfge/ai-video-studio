---
id: 2026-01-12T05-47-37Z-frontend-img2img-model-filter-audit-warnings
date: 2026-01-12T05:47:37Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, image_gen, img2img, ux]
related_paths:
  - ai-pic-frontend/src/components/features/environments/EnvironmentDetailView.tsx
  - ai-pic-frontend/src/components/shared/GenerationAuditWarnings.tsx
  - ai-pic-frontend/src/components/shared/index.ts
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImageSettingsForm.tsx
  - ai-pic-frontend/src/utils/modelSupport.ts
summary: "Hide unsupported img2img models and surface audit warnings in Environment UI"
---

## User Prompt

在前端统一梳理图生图入口：图生图只展示支持参考图的模型，并把后端返回的 audit_warnings 展示出来（例如 keling kling-v2-1 会回退到 kling-v2 的告警）。

## Goals

- 避免在图生图场景误选不支持参考图的模型（减少失败与回退导致的质量波动）。
- 将后端 audit_warnings 透出到 UI，提升可观测性与可解释性。

## Changes

- 图生图设置：`ImageToImageSettingsForm` 通过 `filterModels` 隐藏不支持参考图的模型，并在模型列表加载后自动纠正默认/已选模型到可用项。
- 模型能力判断：新增 `supportsReferenceImage` 工具函数，优先读取模型 metadata 的 UI 标记，其次基于 capabilities/type 兜底判定。
- 审计提示展示：新增 `GenerationAuditWarnings` 组件，并在环境详情页展示 `last_*_generation.audit_warnings`。

## Validation

- Lint: `cd ai-pic-frontend && npm run lint`
- Chrome (MCP) E2E:
  - 登录 `geyunfei / Gyf@845261`
  - 打开 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`
  - 页面顶部展示 “环境图生图提示”，包含 `keling model kling-v2-1 does not support image_to_image; using kling-v2`
  - 点击任意参考图的“图生图”打开弹窗，切换提供商到“可灵”，模型下拉仅包含 “可灵图像生成 V1 / V2”（V2.1 不再出现）

## Next Steps

- 将 `GenerationAuditWarnings` 覆盖到虚拟 IP 图像页与分镜图生图页（同一套告警展示规则）。
- 后端修复并补测试：环境图像持久化对 keling 返回 `{'index','url'}` 结构的兼容（避免 `'dict' object has no attribute 'startswith'`）。

## Linked Commits

- (this commit)
