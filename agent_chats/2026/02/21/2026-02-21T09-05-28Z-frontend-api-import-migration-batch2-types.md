---
id: 2026-02-21T09-05-28Z-frontend-api-import-migration-batch2-types
date: "2026-02-21T09:05:28Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, refactor, api]
related_paths:
  - ai-pic-frontend/src/utils/creator.ts
  - ai-pic-frontend/src/utils/storyOptions.ts
  - ai-pic-frontend/src/utils/scriptGenerationDefaults.ts
  - ai-pic-frontend/src/hooks/storyEpisodeGenerationForm.ts
  - ai-pic-frontend/src/components/shared/MarketingFields.tsx
  - ai-pic-frontend/src/components/features/script/scriptTrafficUtils.ts
  - ai-pic-frontend/src/components/features/stories/StoryCard.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryDetailHeader.tsx
  - ai-pic-frontend/src/components/features/story-detail/StorySummarySection.tsx
  - ai-pic-frontend/src/components/features/story-detail/AdditionalInfoSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/CharactersSection.tsx
  - ai-pic-frontend/src/components/features/script/ScriptHeader.tsx
  - ai-pic-frontend/src/components/features/script/ScriptOverviewTab.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeHeader.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeDetails.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeWorkspaceHeader.tsx
  - ai-pic-frontend/src/components/features/episode/ScriptList.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceOverviewTabContent.tsx
  - ai-pic-frontend/src/components/features/stories/CharacterSelector.tsx
  - ai-pic-frontend/src/components/features/stories/StoryGenerateForm.tsx
  - ai-pic-frontend/src/types/api-extensions.d.ts
  - ai-pic-frontend/src/utils/api/types/voice.types.ts
  - tasks.md
summary: "[refactor] Migrated type-only imports from legacy api barrel to split api/types for low-risk frontend files"
---

## User Prompt

继续

## Goals

- 继续推进前端 API 分层迁移，降低 `@/utils/api` 旧入口引用。
- 优先处理低风险、无行为改动的类型导入文件，形成可独立提交的原子批次。
- 同步更新任务板中的迁移进度。

## Changes

- 将 20 个低风险文件的 `import type ... from "@/utils/api"` 切换到 `@/utils/api/types`（故事/剧集/剧本展示组件、营销字段、默认表单与工具函数）。
- 更新 `ai-pic-frontend/src/types/api-extensions.d.ts`：新增对 `@/utils/api/types` 的模块扩展（`CreatorInfo` 与 `creator` 字段），保证 `Story/VirtualIP/Environment` 在新类型入口下兼容原有扩展字段。
- 兼容修复：更新 `ai-pic-frontend/src/utils/api/types/voice.types.ts` 的 `VoiceConfig` 为新旧字段并集（字段可选），消除 `VirtualIP.voice_config` 在新旧类型间的结构冲突。
- 更新 `tasks.md`：迁移进度改为“已完成 30 处，剩余约 96 处”。

## Validation

- `cd ai-pic-frontend && npm run lint`（通过；仅现有 warning，无新增 error）
- `pre-commit run --files ...`（通过：prettier、ledger enforcement、frontend lint）
- `./docker/build_prod_images.sh`（通过；backend/frontend 双平台构建与推送完成）
- 过程复盘：首次构建失败于 `StorySettingSection`（`VirtualIP.voice_config` 类型不兼容）；补齐 `VoiceConfig` 兼容后重跑构建通过。
- 统计：`from "@/utils/api"` 旧入口引用 116 -> 96

## Next Steps

- 继续迁移 `tasks/*`、`virtual-ip/*` 与 `stories/*` 中仍为类型导入的低风险文件。
- 对含 `AIModelType`/`apiClient` 等运行时依赖的文件，先做兼容映射设计再迁移，避免行为回归。

## Linked Commits

- 待本次提交后补充
