---
id: 2026-02-21T11-54-40Z-frontend-api-import-migration-batch4-runtime-types
date: "2026-02-21T11:54:40Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, refactor, api]
related_paths:
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/components/features/AIGenerationProcess.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentDetailView.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeAspectRatioSelect.tsx
  - ai-pic-frontend/src/components/features/episode/ScriptGenerationForm.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx
  - ai-pic-frontend/src/components/features/script/ScriptTrafficTab.tsx
  - ai-pic-frontend/src/components/features/stories/StoryBasicsSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/EpisodeGeneratePanel.tsx
  - ai-pic-frontend/src/components/features/story-detail/EpisodeListSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelExportSection.tsx
  - ai-pic-frontend/src/components/features/tasks/useTasks.ts
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/VirtualIPImageManager.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPCreateModal.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPListSection.tsx
  - ai-pic-frontend/src/components/layouts/AdminLayout.tsx
  - ai-pic-frontend/src/components/shared/SmartInputField.tsx
  - ai-pic-frontend/src/components/shared/modals/RoleManagementModal.tsx
  - ai-pic-frontend/src/components/shared/modals/UserApprovalModal.tsx
  - ai-pic-frontend/src/components/shared/modals/UserDetailsModal.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/useReferenceSelection.ts
  - ai-pic-frontend/src/hooks/useAvailableModels.ts
  - ai-pic-frontend/src/hooks/useStylePresets.ts
  - ai-pic-frontend/src/hooks/useVirtualIPCreateForm.ts
  - ai-pic-frontend/src/hooks/useVirtualIPList.ts
  - ai-pic-frontend/src/hooks/useVoiceConfigOptions.ts
  - ai-pic-frontend/src/hooks/useVoicePreview.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageActions.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageData.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageUpload.ts
  - ai-pic-frontend/src/types/api-extensions.d.ts
  - ai-pic-frontend/src/utils/api/types/ai-model.types.ts
  - ai-pic-frontend/src/utils/api/types/virtual-ip.types.ts
  - tasks.md
summary: "[refactor] Migrated mixed runtime+type imports from legacy api barrel to split endpoints/types with compatibility aliases"
---

## User Prompt

开始

## Goals

- 继续推进前端 API 分层迁移，进一步减少 `@/utils/api` 旧入口引用。
- 将低风险“运行时 API + 类型”混合导入拆分为 `@/utils/api/endpoints` + `@/utils/api/types`。
- 保持行为不变，补齐兼容类型以避免迁移引入构建回归。

## Changes

- 迁移 33 个前端文件：把 legacy `@/utils/api` 混合导入拆为新分层导入。
- 覆盖模块：environments、virtual-ip、tasks、story detail、episode workspace、admin modals、shared hooks。
- 兼容补齐 `ai-pic-frontend/src/utils/api/types/ai-model.types.ts`：
  - `AIModelType` 增加 legacy 别名键（`Text/Image/Video/...`）与新键并存。
  - `AvailableModelsResponse` 增加 legacy 字段 `default`/`count`，兼容旧调用点。
- 兼容补齐 `ai-pic-frontend/src/utils/api/types/virtual-ip.types.ts`：
  - 对齐 legacy 的 `VirtualIPAIGenerationRequest/Response/DetailedResponse` 与 `AIGenerationDetails` 必填字段。
  - 修复 `CreateVirtualIPRequest/UpdateVirtualIPRequest.voice_config` 类型为 `VoiceConfig`，避免 `Record<string, unknown>` 约束导致构建失败。
- 清理 `ai-pic-frontend/src/types/api-extensions.d.ts` 对 `@/utils/api` 的空导入。
- 更新 `tasks.md` 迁移进度：`@/utils/api` 引用剩余约 27 处。

## Validation

- `cd ai-pic-frontend && npm run lint`（通过；仅现有 warning，无新增 error）
- `pre-commit run --files ...`（通过：prettier、frontend lint、agent_chats 规则检查）
- `./docker/build_prod_images.sh`（通过；backend/frontend 双平台镜像构建与推送完成，结束于 `[build_prod_images] Done.`）
- Chrome MCP 自测（账号 `geyunfei`）：
  - `/login` 登录成功并跳转首页 `/`
  - 打开 `/environments`，确认环境列表与“管理图片/删除”操作入口正常渲染
  - 打开 `/tasks`，确认任务列表正常加载
  - 打开 `/virtual-ip` 并进入 `/virtual-ip/233525e9045146d580a1d18ef4a28161`，确认“虚拟IP详情/配音设置/图片管理”模块正常渲染
- 统计：`from "@/utils/api"` 旧入口引用 67 -> 27
- 复盘：
  - 首次构建失败：`VirtualIPAIGenerationRequest` 缺少 `name`，补齐 `virtual-ip.types.ts` 请求结构。
  - 二次构建失败：`AIGenerationDetails.prompts_used` 可选导致页面类型错误，改为必填并对齐 legacy。
  - 三次构建失败：`CreateVirtualIPRequest.voice_config` 类型过窄，改为 `VoiceConfig` 后构建通过。

## Next Steps

- 继续迁移剩余 27 处：优先 `useScriptDetail`、`WorkspaceScriptTabContent`、`ModelSelector/MultiModelSelector`、`ImageToImageSettingsForm` 等复杂入口。
- 对仍依赖 `apiClient`/默认导出的文件（如 `storyNovelApi.ts`、`register/page.tsx`）评估是改接 `httpClient` 还是保留兼容层。

## Linked Commits

- 待本次提交后补充
