---
id: 2025-12-17T05-30-21Z-frontend-business-id-routing
date: 2025-12-17T05:30:21Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, routing]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/stories/page.tsx
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
summary: "Switch frontend routing/API usage to business_id and keep regen navigation on new records"
---

## User Prompt

- "前端改用 business_id 作为路由/请求主键，并在再生成后跳转到新记录"。
- 需要在再生成时使用响应的新 business_id/id 跳转，并更新 API 参数/路由。

## Goals

- 优先使用 business_id 调用后端（兼容 id），调整页面路由跳转。
- 确保故事/剧集/剧本/虚拟 IP 详情页及关联列表可用 business_id 访问。
- 跑通前端 lint 校验。

## Changes

- API 客户端新增 business_id 解析辅助方法；stories/episodes/scripts/virtual IP 相关的获取/更新/删除/再生成等方法可接受 business_id，列表查询支持 story/episode business_id 参数。
- Stories：列表链接与删除改用 business_id；详情页使用 business_id 加载，子链接（剧集/分镜）切换 business_id。
- Episodes：详情页与分镜页按 business_id 拉取/导航，脚本跳转使用脚本 business_id；剧本再生成仍在当前页刷新。
- Scripts：详情页按 business_id 加载，导出/分镜生成等操作使用业务主键；返回剧集/分镜跳转使用 episode_business_id。
- Virtual IP：列表、详情及图像页按 business_id 访问；图像页先拉取虚拟 IP 以获取 numeric id，再执行图片 CRUD/生成；交互前增加未加载提示。

## Validation

- `npm run lint`（前端）：通过。

## Next Steps

- 观察其他子页（任务等）是否需要展示 business_id；根据后端补充更多 business_id 路由时同步 API 客户端。

## Linked Commits

- (pending)
