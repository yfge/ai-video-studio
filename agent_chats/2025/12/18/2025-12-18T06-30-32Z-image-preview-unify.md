---
id: 2025-12-18T06-30-32Z-image-preview-unify
date: 2025-12-18T06:30:32Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, images, environments, storyboard, virtual-ip]
related_paths:
  - ai-pic-frontend/src/components/ImagePreviewCard.tsx
  - ai-pic-frontend/src/components/ImageToImageModal.tsx
  - ai-pic-frontend/src/app/environments/[id]/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Unified image cards with preview/img2img actions across environments, virtual IPs, and storyboard keyframes."
---

## User Prompt
环境/IP/分镜的图片需要统一的预览/放大/图生图组件，环境图生图弹窗的参考图也要能预览。

## Goals
- 提供一个共享的图片卡片组件，支持预览/放大、图生图入口、统一样式。
- 将环境、虚拟IP以及分镜关键帧的图片位切换到该组件，并在图生图弹窗里补充参考图预览。
- 确认前端构建通过并记录产物构建。

## Changes
- 新增 `ImagePreviewCard` 组件，内置悬浮操作区（图生图、删除、自定义操作）和全屏预览。
- 环境详情与虚拟 IP 图片页改用统一卡片，图生图与删除入口内聚到卡片浮层；文生/图生图弹窗可直接预览参考图。
- 分镜页的首/尾关键帧以及候选图切换为统一卡片，支持一键预览、在卡片上直接发起首帧/尾帧定向图生图，候选图用浮层动作设置为首/尾帧。
- `ImageToImageModal` 支持参考图“预览”浮层；分镜图生图入口可预置参考图并切换生成目标（首/尾）。

## Validation
- `npm run lint` (ai-pic-frontend)
- `./docker/build_prod_images.sh` （tag 588d0e4）
- Chrome DevTools：登录 `geyunfei` → 环境列表 → 打开“办公室”详情 → 点击图片弹出预览浮层；在“图生图”弹窗点击“预览”查看参考图后关闭，流程正常。

## Next Steps
- 部署前端镜像 `588d0e4`，确认分镜页新卡片在实际分镜数据上运行正常。

## Linked Commits
- (pending)
