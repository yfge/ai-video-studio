---
id: 2025-12-17T05-02-12Z-backend-business-id-routes
date: 2025-12-17T05:02:12Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip.py
  - tasks.md
summary: "Add business_id-aware routes and soft-delete guards for key backend endpoints"
---

## User Prompt

- 后端按 business_id 支持获取/更新/删除/再生成，并扩展软删过滤；前端将切换业务主键。

## Goals

- 提供 stories/episodes/scripts/virtual IP 通过 business_id 访问的兼容路由。
- 保持软删过滤与权限校验，避免暴露已删除数据。
- 为后续前端 business_id 路由切换铺路。

## Changes

- Stories: 新增 business_id 版 get/update/delete/characters 路由，统一软删校验并改为 soft delete。
- Episodes: 补充 business_id 解析（含 story 过滤）、get/update/delete/regenerate 业务路由和共享重生成逻辑，列表默认排除软删。
- Scripts: 提供 business_id 获取/更新/删除/重新生成及按 episode business_id 拉取脚本，列表默认过滤软删并支持 episode_business_id 查询。
- Virtual IP: 支持按 business_id 的 get/update/delete，并允许列表按 business_id 过滤。
- Tasks board：添加“business_id 路由/查询参数补全”待办以跟踪剩余端点。

## Validation

- 未运行自动化测试；变更为路由与查询过滤层。

## Next Steps

- 前端路由与 API 调用切换到 business_id，并在再生成后跳转新记录。
- 视需要为其他端点（images 等）补 business_id 路由并补充测试。

## Linked Commits

- (pending)
