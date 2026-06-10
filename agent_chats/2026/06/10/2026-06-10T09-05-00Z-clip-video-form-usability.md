---
id: 2026-06-10T09-05-00Z-clip-video-form-usability
date: "2026-06-10T09:05:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - timeline
  - ux
related_paths:
  - ai-pic-frontend/src/components/features/episode/TimelineClipVideoReworkCard.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipVideoReworkFields.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCardSections.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspace.tsx
  - ai-pic-frontend/tests/timelineClipReworkControls.test.ts
summary: 片段生产表单友好化：视频模型改为可用模型下拉、画面比例改为预设下拉、所有字段加中文标签与提示文本、参考来源逐项帮助说明、Panel 数改为宫格友好下拉。
---

# Clip Video Form Usability

## User Prompt

调整优化片段生产 UI 做到用户友好。原表单是无标签的裸输入框（model/ratio 要手填精确字符串、字段含义不明、参考来源选项无解释）。

## Goals

- 视频模型从裸文本框改为后端可用模型下拉（含「自动选择模型」默认项）。
- 画面比例改为预设下拉（自动/9:16/16:9/1:1/4:3/3:4）。
- 全部字段加中文标签和提示：提示词留空回退分镜规划、时长留空用片段时长、重做原因写入资产履历。
- 视频参考来源按当前选项显示帮助说明；故事板 Panel 选项不可用时说明原因。
- 故事板卡片：画面风格/Panel 数加标签，Panel 数改为 2/3/4/6/8/9 宫格下拉。

## Changes

- 新增 `TimelineClipVideoReworkFields`：`VideoActionSelect`（带动作分类说明）、`VideoModelSelect`（provider:model 值规则与时间轴主面板一致）、`VideoResolutionSelect`、`VideoRatioSelect` 与共享样式常量。
- `TimelineClipVideoReworkCard` 重写为全标签布局并瘦身到 250 行内。
- `TimelineClipProviderReworkCardSections`：`VideoReferenceSelect` 增加逐选项帮助文案（含 legacy `storyboard_grid_panel`）；故事板风格/Panel 数/附加参考图加标签。
- `EpisodeTimelineWorkspace` 通过 `useAvailableModels({ modelType: "video" })` 拉取视频模型并沿 ProductionPanel → Controls → Cards 下传。
- 测试：两卡片渲染用例补断言（模型下拉项、比例预设、画面风格、重做动作标签）。

## Validation

- `npm run test`：57 个测试全部通过。
- `npm run lint`：0 errors。
- `npm run build`：通过（修复 `TimelineVideoReferenceChoice` 帮助文案缺 `storyboard_grid_panel` 的类型错误后）。

## Next Steps

- 跑一轮真实浏览器链路验证（登录 → 选中 video clip → 生成故事板 → 视频 rework），证据落 `artifacts/runs/`。
- `./docker/build_prod_images.sh` 在本系列提交结束后统一执行。

## Linked Commits

- This commit.
