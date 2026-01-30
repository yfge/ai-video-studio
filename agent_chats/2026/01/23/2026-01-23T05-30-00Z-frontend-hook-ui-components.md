---
id: 2026-01-23T05-30-00Z-frontend-hook-ui-components
date: 2026-01-23T05:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, short_drama, hooks, ui]
related_paths:
  - ai-pic-frontend/src/components/features/hooks/index.ts
  - ai-pic-frontend/src/components/features/hooks/HookTagBadge.tsx
  - ai-pic-frontend/src/components/features/hooks/AdSnippetCard.tsx
  - ai-pic-frontend/src/components/features/hooks/HookPlanPanel.tsx
  - ai-pic-frontend/src/components/features/StoryboardFrameCard.tsx
  - tasks.md
summary: "新增前端 hook 可视化组件：HookTagBadge、AdSnippetCard、HookPlanPanel，更新 StoryboardFrameCard 显示 hook 标签"
---

## User Prompt

继续推进「短剧微类型闭环」的前端工作：在分镜/时间线 UI 标注与 hook 节点/投流素材对应的镜头与时间点

## Goals

1. 创建 Hook 可视化组件
2. 在分镜帧上显示 hook 标签
3. 提供投流素材预览组件
4. 提供 Hook 计划面板组件

## Changes

### 新增组件 (src/components/features/hooks/)

**HookTagBadge.tsx** (~130 行)

- Hook 类型徽章组件
- 支持 11 种 hook 类型：hook/reversal/payoff/cliffhanger/betrayal/reveal/revenge/reunion/threat/taboo/power-shift
- 支持强度显示（low/medium/high）
- 每种类型有独立的颜色和图标

**AdSnippetCard.tsx** (~140 行)

- 投流素材卡片组件
- 支持紧凑模式和完整模式
- 显示：时长徽章（15s/30s/60s）、核心台词、视觉钩子、镜头列表、CTA

**HookPlanPanel.tsx** (~200 行)

- Hook 计划面板组件（可折叠）
- 显示：开场钩子、情绪升级、爽点释放、关键反转列表、悬念卡点、投流素材预览

### 更新 StoryboardFrameCard.tsx

- 新增字段：`hook_tag`, `hook_intensity`, `ad_snippet_id`, `start_ms`, `end_ms`
- 在 FrameCard 头部显示 HookTagBadge
- 新增 `formatMs` 函数，显示时间窗（MM:SS.ms 格式）

## Validation

```bash
cd ai-pic-frontend && npm run lint
# 结果：0 errors, 7 warnings
```

## Next Steps

1. **集成到 storyboard/page.tsx**

   - 在页面顶部添加 HookPlanPanel 展示剧集的 hook 计划
   - 在帧生成时填充 hook_tag（从 beat_type 或 scene notes 推断）

2. **Timeline 集成**

   - 在 Timeline 组件中标注 hook beat 边界
   - 与 ad_snippets 的 source_timecode 对应

3. **API 集成**
   - 调用 `/api/v1/scoring/traffic-sheet` 获取投流素材
   - 在 HookPlanPanel 中展示生成的素材

## Linked Commits

- `85d3426` feat(frontend): add hook visualization components for storyboard
