---
id: 2026-01-29T08-41-53Z-frontend-episode-aspect-ratio-default
date: "2026-01-29T08:41:53Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, storyboard, aspect-ratio]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/api/types/story.types.ts
summary: "Prefer Episode.aspect_ratio over Story default for storyboard video modal defaults (frontend)."
---

## User Prompt

屏幕比/画幅：默认 9:16，仅支持 9:16/16:9；Episode/Story 作为默认值层级，且允许生成时临时覆盖。

## Goals

- 前端在“生成视频”弹窗默认画幅上，优先继承 Episode 的画幅覆盖；否则回退 Story 默认画幅。
- 补齐前端类型，避免构建期因字段缺失导致 Next.js build 失败。

## Changes

- `ai-pic-frontend/src/utils/api/types/story.types.ts`
  - Episode 类型补充 `aspect_ratio?: "9:16" | "16:9" | null`。
- `ai-pic-frontend/src/utils/api.ts`
  - 保持 legacy `Episode` 类型同步增加 `aspect_ratio`（当前大量页面仍引用该入口）。
- `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`
  - `StoryboardVideoModal` 的 `defaultRatio` 改为 `episode?.aspect_ratio ?? story?.default_aspect_ratio`。

## Validation

- `cd ai-pic-frontend && npm run lint`（仅 warnings）
- `cd ai-pic-frontend && npm run build`
- `./docker/build_prod_images.sh`
- Chrome（MCP）冒烟：
  - 打开 `http://localhost:8089/episodes/131/storyboard` 页面正常渲染

## Next Steps

- 在 UI 增加 Episode 画幅设置入口（含“继承 Story 默认”选项），并补 9:16/16:9 各 1 条真实视频生成抽检（`ffprobe`）。

## Linked Commits

- (pending)
