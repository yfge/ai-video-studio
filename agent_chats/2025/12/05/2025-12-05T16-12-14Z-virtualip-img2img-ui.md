---
id: 2025-12-05T16-12-14Z-virtualip-img2img-ui
date: 2025-12-05T16:12:14Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, virtual-ip, image]
related_paths:
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Allow Virtual IP images to be used as img2img sources for back/full-body variants"
---
## User Prompt
更改前端 交互，比如已经有了图以后可以用图生图，生成背面照全身照等

## Goals
- When a Virtual IP already has images, allow operators to trigger image-to-image generation for variations (e.g., back view, full body).
- Reuse existing model selection while keeping the UX lightweight and non-destructive.

## Changes
- Added `virtualIPImageAPI.generateVariantFromImage` that calls the new `/api/v1/ai/generate/image-to-image` backend endpoint.
- On the Virtual IP image management page, introduced a `图生图` button per image that opens a small overlay where users can enter a variant prompt (back view / full body / pose, etc.).
- Variants are generated via img2img and returned as URLs, opened in a new tab and surfaced via success alerts, without auto-saving into the assets library yet.

## Validation
- ai-pic-frontend: `npm run lint`

## Next Steps
- Optionally add a "保存为资产" flow that lets users import a generated variant URL back into `virtual_ip_images`.
- Extend the UI to offer quick preset prompts like "背面照" / "全身照" / "动作连拍" as chips.

## Linked Commits
- (pending)
