---
id: 2025-12-17T04-18-50Z-soft-delete-filters-round4
date: 2025-12-17T04:18:50Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/app/services/user_management_service.py
  - ai-pic-backend/app/api/v1/endpoints/admin.py
summary: "Extended soft-delete filtering to story structure services and admin user management"
---

## User Prompt

- “将软删过滤补全到剩余端点（story_structure、admin/diagnostic 等涉及业务数据）。”

## Goals

- story_structure 查询默认排除软删。
- 管理端/用户管理服务过滤软删用户。

## Changes

- `story_structure_service`: 添加 `_not_deleted`，对 treatments/script/scenes/beats/shots 查询统一加软删过滤。
- `user_management_service`: 列表、审批、角色更新、暂停等操作仅作用于未软删用户。
- `admin.py`: 详情查询过滤软删。

## Validation

- 未运行自动化测试（逻辑调整需后续覆盖）。

## Next Steps

- 继续检查剩余端点（若有）并运行 pytest 验证。

## Linked Commits

- (pending)
