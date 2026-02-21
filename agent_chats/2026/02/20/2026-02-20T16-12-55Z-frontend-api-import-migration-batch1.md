---
id: 2026-02-20T16-12-55Z-frontend-api-import-migration-batch1
date: "2026-02-20T16:12:55Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, refactor, api]
related_paths:
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
  - ai-pic-frontend/src/hooks/useStories.ts
  - ai-pic-frontend/src/hooks/useEpisodeDetail.ts
  - ai-pic-frontend/src/hooks/useStoryEpisodeGeneration.ts
  - ai-pic-frontend/src/hooks/useNormalizedScenes.ts
  - ai-pic-frontend/src/hooks/useScriptStructure.ts
  - ai-pic-frontend/src/hooks/storyDetailUtils.ts
  - ai-pic-frontend/src/hooks/episodeDetailUtils.ts
  - ai-pic-frontend/src/hooks/useEpisodeMetadata.ts
  - ai-pic-frontend/src/hooks/useTaskPolling.ts
  - ai-pic-frontend/src/utils/api/types/script.types.ts
  - ai-pic-frontend/src/utils/api/types/story.types.ts
  - ai-pic-frontend/src/utils/api/types/virtual-ip.types.ts
  - tasks.md
summary: "Migrated first frontend hooks batch from legacy api barrel to new endpoints/types modules"
---

## User Prompt

继续

## Goals

- 继续执行前端 API 分层迁移，减少对 legacy `@/utils/api` 聚合入口的依赖。
- 在不改变业务逻辑的前提下，先迁移 hooks 层一批低风险 import。
- 更新任务看板中的迁移进度说明。

## Changes

- 将以下 hooks 从 `@/utils/api` 迁移到新分层导入：
  - `@/utils/api/endpoints`
  - `@/utils/api/types`
- 迁移文件：
  - useStoryDetail.ts
  - useStories.ts
  - useEpisodeDetail.ts
  - useStoryEpisodeGeneration.ts
  - useNormalizedScenes.ts
  - useScriptStructure.ts
  - storyDetailUtils.ts
  - episodeDetailUtils.ts
  - useEpisodeMetadata.ts
  - useTaskPolling.ts
- `useScriptDetail.ts` 暂未纳入本批迁移（当前文件 277 行，超过 AGENTS 限制，待先拆分再迁移）。
- 为保证新旧类型并存阶段可编译，补齐 split types 与 legacy `src/utils/api.ts` 的兼容字段：
  - `script.types.ts`：补齐 `dialogue_style`、`scene_detail_level`、`market_region`、`micro_genre`、`hook_plan`、`ad_snippets` 等脚本生成请求字段。
  - `story.types.ts`：将 `Story.is_public` 调整为必填；补齐 `StoryCharacter` 的 legacy 必需字段并收敛可空差异。
  - `virtual-ip.types.ts`：对齐 `VirtualIP` 可空性（如 `default_avatar_url`），并收敛 `voice_config` 类型到 `VoiceConfig`。
- `tasks.md` 更新：在“迁移至少 60 处旧入口引用”条目补充本批进度（hooks 首批 10 处）。

## Validation

- `cd ai-pic-frontend && npm run lint`（通过；仅现有 warning，无新增 error）
- `pre-commit run --files ...`（通过：prettier、ledger enforcement、frontend lint 均通过）
- `./docker/build_prod_images.sh`（通过；backend/frontend 双平台构建与推送完成）
- 首次/中间构建失败复盘并修正：
  - `ScriptGenerationRequest` 缺少 `dialogue_style/scene_detail_level`
  - `Story.is_public` 新旧定义可选性不一致
  - `VirtualIP.default_avatar_url` 新旧定义可空性不一致
  - 对应类型兼容修复后重新构建通过
- 统计检查：`from "@/utils/api"` 旧入口引用降至约 116 处（继续迁移中）。

## Next Steps

- 继续迁移组件层高频 `@/utils/api` 引用（优先 story/episode/script/task/admin）。
- 启动 `src/utils/api.ts` 瘦身，逐步收敛为兼容层。

## Linked Commits

- 待本次原子提交后补充
