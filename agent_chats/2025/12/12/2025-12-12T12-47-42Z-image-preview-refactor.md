---
id: 2025-12-12T12-47-42Z-image-preview-refactor
date: 2025-12-12T12:47:42Z
participants: [human, codex]
models: [gpt-5.1]
tags: [frontend, ui, gallery]
related_paths:
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/components/ImagePreviewModal.tsx
summary: "Refined virtual IP / environment / storyboard image tiles to show full thumbnails and added shared lightbox preview."
---

## User Prompt

现在在人物IP，场景，分镜都有图片显示 图片显示 的结构还是太糙了，现在做一下重构：1. 在小格时可以显示全部而不是显示一部分 2. 添加点击时看大图的效果

## Goals

1. 调整人物IP、场景、分镜图片格子的展示方式，使缩略图不再被裁切。
2. 支持点击缩略图查看大图，提升查看细节的体验。

## Changes

- 新增通用的 `ImagePreviewModal` 组件（支持 ESC 关闭、遮罩点击关闭），用于各处的图片放大预览。
- 虚拟IP图像管理页：缩略图改为等比 `object-contain`，点击进入大图预览，并保留 OSS/CDN 回退处理。
- 环境列表：参考图缩略图改为完整展示，并在悬停操作区新增“预览”按钮；同样使用新预览弹窗。
- 分镜工作台：分镜图预览改为完整展示、可点击放大，同时保留新标签打开能力。

## Validation

- `npm run lint` （通过，存在既有的 unused eslint-disable 提示：`episodes/[id]/storyboard/page.tsx` 与 `scripts/[id]/page.tsx`）
- 未进行 Chrome 端到端验证：本次为静态 UI 改造，当前未启动前后端服务。

## Next Steps

- 待后端启动后，在浏览器实际点击虚拟IP/环境/分镜缩略图确认预览弹窗展示正常。

## Linked Commits

- feat(frontend): add image preview modal
