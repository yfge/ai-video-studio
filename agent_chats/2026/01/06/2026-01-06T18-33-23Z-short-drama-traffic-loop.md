---
id: 2026-01-06T18-33-23Z-short-drama-traffic-loop
date: 2026-01-06T18:33:23Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, feature, traffic-loop, micro-genre]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - ai-pic-frontend/src/components/features/episode/ScriptGenerationForm.tsx
  - ai-pic-frontend/src/components/features/index.ts
  - ai-pic-frontend/src/components/features/script/index.ts
  - ai-pic-frontend/src/components/features/script/ScriptTrafficTab.tsx
  - ai-pic-frontend/src/components/features/script/scriptTrafficUtils.ts
  - ai-pic-frontend/src/components/features/stories/StoryGenerateForm.tsx
  - ai-pic-frontend/src/components/features/stories/StoryBasicsSection.tsx
  - ai-pic-frontend/src/components/features/stories/StorySettingSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/EpisodeGeneratePanel.tsx
  - ai-pic-frontend/src/components/shared/index.ts
  - ai-pic-frontend/src/components/shared/MarketingFields.tsx
  - ai-pic-frontend/src/hooks/episodeDetailUtils.ts
  - ai-pic-frontend/src/hooks/scriptDetailUtils.ts
  - ai-pic-frontend/src/hooks/scriptTabs.ts
  - ai-pic-frontend/src/hooks/storyDetailUtils.ts
  - ai-pic-frontend/src/hooks/useEpisodeDetail.ts
  - ai-pic-frontend/src/hooks/useEpisodeMetadata.ts
  - ai-pic-frontend/src/hooks/useNormalizedScenes.ts
  - ai-pic-frontend/src/hooks/useScriptDetail.ts
  - ai-pic-frontend/src/hooks/useScriptStructure.ts
  - ai-pic-frontend/src/hooks/useStories.ts
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
  - ai-pic-frontend/src/hooks/useTaskPolling.ts
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/marketingTemplates.ts
  - ai-pic-frontend/src/utils/scriptGenerationDefaults.ts
  - ai-pic-frontend/src/utils/storyOptions.ts
  - tasks.md
summary: "Added micro-genre traffic metadata fields and a traffic tab across story/episode/script generation."
---

## User Prompt

实施短剧微类型与投流驱动创作闭环（故事→剧本→时间线→分镜）并完成 Chrome 全流程生成验证，保持提交原子性与工作区干净。

## Goals

- 接入市场/微类型/Hook 计划/投流素材等营销字段并贯穿故事、剧集、剧本生成流程。
- 新增投流/评分展示与导出视图，便于验证投流素材与评分数据。
- 完成真实浏览器端到端生成验证并记录结果。

## Changes

- 新增投流字段输入组件与故事生成表单分区，统一市场/微类型/Hook/素材的输入结构。
- 在剧集、剧本生成表单补齐营销字段并透传到生成请求。
- 增加剧本“投流/评分”标签页及相关格式化工具，支持投流素材 CSV 导出。
- 抽取剧集、剧本、故事详情页的状态/结构化数据处理为独立 hooks/utils。
- 补齐脚本详情类型导出，并修正投流素材字符串过滤逻辑以通过构建校验。
- 更新任务清单进度标记。

## Validation

- `npm run lint` (warnings only in `src/components/features/episode/WorkspaceStoryboardTabContent.tsx` about unused vars and `<img>` usage).
- `./docker/build_prod_images.sh` (backend + frontend images built/pushed; frontend build succeeds with existing lint warnings).
- Chrome (MCP) E2E: 登录 `geyunfei`, 创建故事“微类型投流验证-1”并生成剧集、生成剧本（script 72）、执行时间线一键流水线、分镜图像批量生成；任务 508 完成后刷新分镜页，`img` 数量 235，已显示生成内容。

## Next Steps

- 排查脚本详情“投流/评分”页的微类型字段展示为“未指定”的原因（可能是后端未回写 `generation_params` 或 `extra_metadata`）。
- 若要清理现有 lint 警告，集中处理 `WorkspaceStoryboardTabContent.tsx` 未使用变量与 `<img>` 规则。

## Linked Commits

- (pending)
