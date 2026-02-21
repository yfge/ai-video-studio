---
id: 2026-02-21T09-18-03Z-frontend-api-import-migration-batch3-types
date: "2026-02-21T09:18:03Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, refactor, api]
related_paths:
  - ai-pic-frontend/src/components/features/environments/EnvironmentHeader.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentList.tsx
  - ai-pic-frontend/src/components/features/episode/ShortDramaScriptTemplateSelector.tsx
  - ai-pic-frontend/src/components/features/stories/StorySettingSection.tsx
  - ai-pic-frontend/src/components/features/tasks/TaskDetails.tsx
  - ai-pic-frontend/src/components/features/tasks/TasksList.tsx
  - ai-pic-frontend/src/components/features/tasks/TasksPage.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-detail/VirtualIPAdditionalInfoSection.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-detail/VirtualIPInfoSection.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-detail/VoiceSettingsPanel.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGrid.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImagePageHeader.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPVoiceSettingsForm.tsx
  - ai-pic-frontend/src/components/shared/ImageGenAdvancedFields.tsx
  - ai-pic-frontend/src/components/shared/ImageModelUiFields.tsx
  - ai-pic-frontend/src/components/shared/ModelUiFields.tsx
  - ai-pic-frontend/src/components/shared/StyleSpecAdvancedPanel.tsx
  - ai-pic-frontend/src/components/shared/VideoModelUiFields.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImageStyleFields.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/useImageToImageModalState.ts
  - ai-pic-frontend/src/hooks/useVirtualIPImages.ts
  - ai-pic-frontend/src/hooks/virtual-ip/virtualIpImageConstants.ts
  - ai-pic-frontend/src/utils/api/types/ai-model.types.ts
  - ai-pic-frontend/src/utils/api/types/voice.types.ts
  - ai-pic-frontend/src/utils/modelSupport.ts
  - ai-pic-frontend/src/utils/modelUiImage.ts
  - ai-pic-frontend/src/utils/modelUiImageGen.ts
  - ai-pic-frontend/src/utils/modelUiVideo.ts
  - ai-pic-frontend/src/utils/virtual-ip/createFormUtils.ts
  - ai-pic-frontend/src/utils/virtual-ip/types.ts
  - tasks.md
summary: "[refactor] Migrated additional type-only imports to split api/types and reduced legacy api barrel references"
---

## User Prompt

继续

## Goals

- 继续推进前端 API 分层迁移，减少 `@/utils/api` 旧入口引用。
- 仅迁移 type-only 导入文件，避免运行时行为变化。
- 同步更新任务板迁移进度。

## Changes

- 迁移 28 个 type-only 文件：将 `import type ... from "@/utils/api"` 切换到 `@/utils/api/types`。
- 覆盖模块：环境、任务、虚拟 IP 详情/图片、共享模型 UI、image-to-image 子模块、若干 hooks 与 utils。
- 兼容修复：放宽 `ai-pic-frontend/src/utils/api/types/voice.types.ts` 类型约束，兼容 legacy `VoiceEnums.defaults` / `VoiceList` / `VoicePreviewResponse` 等返回结构。
- 兼容修复：调整 `ai-pic-frontend/src/utils/api/types/ai-model.types.ts` 的 `AIModel` 结构（`model_id`、`id?`、`type: string`、`capabilities: string[]`），兼容仍使用 legacy API 形状的页面。
- 更新 `tasks.md`：迁移进度调整为“已完成 58 处，剩余约 67 处”。

## Validation

- `cd ai-pic-frontend && npm run lint`（通过；仅现有 warning，无新增 error）
- `pre-commit run --files ...`（通过：prettier、frontend lint、agent_chats 规则检查）
- `./docker/build_prod_images.sh`（通过；backend/frontend 镜像构建完成）
- 过程复盘：
  - 首次构建失败于 `VirtualIP` 页面，报 `VoiceEnums.defaults` 类型不兼容；放宽 `voice.types.ts` 后修复。
  - 二次构建失败于 `EnvironmentGenerationFields`，报 `AIModel.id` 类型不兼容；调整 `ai-model.types.ts` 后修复。
  - 三次构建通过，输出 `[build_prod_images] Done.`。
- Chrome MCP 自测（账号 `geyunfei`）：
  - 登录 `/login` → 首页 `/`
  - 进入 `/tasks` 列表页
  - 进入 `/virtual-ip` 列表页
  - 点击“查看详情”进入 `/virtual-ip/233525e9045146d580a1d18ef4a28161`，确认“虚拟IP详情 / 配音设置 / 图片管理”模块正常加载
- 统计：`from "@/utils/api"` 旧入口引用 96 -> 67

## Next Steps

- 继续迁移 `hooks/*` 和 `components/*` 中“运行时 + 类型”混合导入文件，按 `endpoints` + `types` 双入口拆分。
- 保留 `AIModelType`、`apiClient` 等运行时依赖在 legacy 入口，待兼容层完成后再迁移。

## Linked Commits

- 待本次提交后补充
