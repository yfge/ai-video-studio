---
id: 2026-06-10T08-20-00Z-reference-image-default-selection
date: "2026-06-10T08:20:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - timeline
  - clip-storyboard
  - ux
related_paths:
  - ai-pic-frontend/src/components/features/episode/TimelineClipStoryboardReferenceImagesModel.ts
  - ai-pic-frontend/src/components/features/episode/useTimelineClipStoryboardReferenceSelection.ts
  - ai-pic-frontend/src/components/features/episode/TimelineClipStoryboardReferenceImages.tsx
  - ai-pic-frontend/tests/timelineClipReworkControls.test.ts
  - ai-pic-frontend/tests/timelineWorkspaceLayout.test.tsx
summary: 故事板/视频生成的 IP 图与环境图改为前端智能默认勾选（每个已选 IP 默认第一张、环境默认第一张），保留手动增删并新增全选/清空与选中计数。
---

# Reference Image Default Selection And Bulk Controls

## User Prompt

完成分镜生成链路中的 IP 图/环境图绑定体验。用户明确要求：参考图在前端可选择，不做后端全自动注入。原实现要求逐张手动点选缩略图，否则生成请求不携带任何角色/环境参考。

## Goals

- 选中角色 IP 后，默认自动勾选每个 IP 的第一张图作为参考锚点。
- 选定场景环境后，默认自动勾选第一张环境参考图。
- 保留完整手动控制：单击取消勾选、全选、清空；用户取消后不会被自动重选。
- 显示「已选 n/m」计数，让绑定状态一目了然。

## Changes

- `TimelineClipStoryboardReferenceImagesModel`：新增 `applyCharacterReferenceImageDefaults`（保留仍有效的手动选择，仅为没有任何选中图的已选 IP 补默认第一张）与 `applyEnvironmentReferenceImageDefaults`（选择为空时默认第一张环境图）。
- `useTimelineClipStoryboardReferenceSelection`：将原 prune 副作用替换为默认选择副作用（依赖仅在选项加载或 IP 选择变化时触发，单击取消不会被覆盖）；新增 `handleStoryboardCharacterReferenceImagesReplace` / `handleStoryboardEnvironmentReferenceImagesReplace`。
- `TimelineClipStoryboardReferenceImages`：每个图片网格新增「已选 n/m，选中的图会作为生成参考」计数行与「全选 / 清空」按钮（带无障碍标签）。
- 测试更新：原手动点选用例改为断言默认勾选（`aria-pressed="true"`）后直接提交；新增「取消默认勾选 + 环境图清空后 payload 不携带参考图」用例；`timelineWorkspaceLayout` 的环境绑定用例同步改为默认勾选断言。

## Validation

- `npm run test`：57 个测试全部通过。
- `npm run lint`：0 errors（3 条无关既有 warnings）。
- `npm run build`：通过。

## Next Steps

- 视频表单友好化：模型下拉、比例预设、字段说明文本。

## Linked Commits

- This commit.
