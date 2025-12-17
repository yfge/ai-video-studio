---
id: 2025-12-17T15-25-50Z-env-frontend-detail
date: 2025-12-17T15:25:50Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, environment]
related_paths:
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/app/environments/[id]/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Move environment image management into a detail page, add upload support, and align list UI"
---

## User Prompt

1. 环境列表 不再显示所有的环境图片，增环境详情的页面，在里面进行管理
2. 环境也支持图片上传
3. 所有的 API 接口统一检查，增加 DTO 层，相应字段非必要不返回！

## Goals

- Stop rendering all environment images in the list view and manage them in a dedicated detail page.
- Allow environment reference image upload from the frontend using the new backend endpoint.
- Keep creation flow consistent while reducing payload from the list API.

## Changes

- Simplified environment list page to a summary-only view with links to a new detail page; removed inline image rendering and AI generate controls, keeping the shared creation overlay.
- Added environment detail page (`/environments/[id]`) to show metadata, list/delete reference images, upload new images via OSS-backed API, and trigger async AI generation.
- Extended API client with `getEnvironment` and `uploadEnvironmentImage` helpers for the new flows.

## Validation

- `npm run lint` ✅
- Manual browser spot-check not run after this change (backend mock already stopped); UI verified by code review.

## Next Steps

- Re-test in a live backend to confirm upload + async generation work end-to-end and that the list view stays lightweight.

## Linked Commits

- TBC: environment detail UI and upload wiring
