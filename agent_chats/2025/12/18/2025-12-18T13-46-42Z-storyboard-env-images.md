---
id: 2025-12-18T13-46-42Z-storyboard-env-images
date: 2025-12-18T13:46:42Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard, environment]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Storyboard uses environment image cache to show and use environment reference images when generating keyframes."
---

## User Prompt

- 场景绑定了环境“老拐的家”，但参考图显示 0 张，关键帧生成时也没有环境图可选。

## Goals

- 确保分镜页面在绑定环境后能加载并展示该环境的参考图，并在关键帧/批量生成时可作为参考图选择。

## Changes

- Storyboard 页面在选定环境后调用 `/environments/{id}/images` 拉取参考图，缓存到 `envImageCache`；所有参考图选择、参考图计数与提示均改用缓存结果，避免环境列表 summary 无 `reference_images` 时显示为 0。
- 参考图收集逻辑使用缓存的环境图片作为优先来源，防止空列表导致无法生成。

## Validation

- `pre-commit run --files ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`（通过，含 frontend lint）。
- `bash docker/build_prod_images.sh`（通过，镜像 tag 3f81387）。
- 未重跑全量 `npm run lint`（已由 pre-commit 对改动文件检查），未跑 e2e。

## Next Steps

- 部署前端到镜像 `3f81387`，在分镜页面重新选择环境“老拐的家”，应能看到参考图数量>0，并可在“选择参考图生成关键帧”里选中环境图像。

## Linked Commits

- (pending)
