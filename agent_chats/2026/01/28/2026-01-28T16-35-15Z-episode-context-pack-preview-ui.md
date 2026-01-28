---
id: 2026-01-28T16-35-15Z-episode-context-pack-preview-ui
date: 2026-01-28T16:35:15Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, episode, context-pack]
related_paths:
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
  - ai-pic-frontend/src/components/features/story-detail/EpisodeContextPackPreview.tsx
  - ai-pic-frontend/src/components/features/story-detail/EpisodeGeneratePanel.tsx
  - ai-pic-frontend/src/hooks/storyEpisodeGenerationForm.ts
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
  - ai-pic-frontend/src/hooks/useStoryEpisodeGeneration.ts
  - tasks.md
summary: "Add Context Pack preview + toggles to story episode generation UI."
---

## User Prompt

继续按 `tasks.md` 推进：在“生成剧集/再生成”位置提供上下文预览与开关。

## Goals

- 在 Story 详情页的“生成剧集”区域增加 Context Pack 预览能力（不调用模型）。
- 提供开关：continuity ledger / 角色卡 / 最近 N 集摘要。
- 保持文件大小合规（hooks/组件不超限），并更新 `tasks.md` 进度。

## Changes

- 新增 `EpisodeContextPackPreview` 组件：展示开关与 JSON 预览（折叠区）。
- 抽出 `useStoryEpisodeGeneration`：集中管理剧集生成表单/异步开关/提示词预览/Context Pack 预览逻辑。
- `useStoryDetail` 退回到“加载故事/剧集/剧本 + 导航”，并组合 `useStoryEpisodeGeneration` 输出。
- Story 详情页接入 `contextPackPreviewProps` 传递给 `EpisodeGeneratePanel`。
- 更新 `tasks.md`：Phase 2 Context Pack 前端项标记完成。

## Validation

- `cd ai-pic-frontend && npm run lint`
- `./docker/build_prod_images.sh`
- Chrome (MCP):
  - 登录 `geyunfei / Gyf@845261`
  - 进入 Story：`/stories/cd0843195eb54cc28a7e3c9b0f8def63`
  - 展开“生成剧集” → 打开“上下文预览（Context Pack）” → 点击“预览上下文”
    - `POST /api/v1/episodes/context-pack/preview` 返回 200，页面展示 Context Pack JSON（包含 `meta.version=v1`、`character_cards`、`recent_episodes` 等字段）
    - 关闭“角色卡”后再次预览：`character_cards.length` 从 1 变为 0
    - “最近摘要”改为 0 后再次预览：`recent_episodes.length` 从 3 变为 0
    - 注：当前样例 Story 的 `continuity_ledger` 返回为 `null`（开/关均为 `null`），因此未以该字段做差异验证

## Next Steps

- Phase 2 验证：同一 Story 连续生成/再生成 2 次 episode，抽检关键设定一致性与 ledger 更新（Chrome 记录）。
- 如需让开关影响实际生成：后端异步 episode 生成也需要读取这些选项来构建 context pack（当前开关只影响预览 API）。

## Linked Commits

- (pending)
