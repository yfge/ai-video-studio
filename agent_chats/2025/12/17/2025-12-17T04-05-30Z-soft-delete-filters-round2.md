---
id: 2025-12-17T04-05-30Z-soft-delete-filters-round2
date: 2025-12-17T04:05:30Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip.py
  - ai-pic-backend/app/api/v1/endpoints/tasks.py
  - ai-pic-backend/app/api/v1/endpoints/auth.py
summary: "Extend soft-delete filtering to stories/virtual IP/tasks/users and add business-layer duplicate checks"
---

## User Prompt

- 将软删过滤扩展到故事、虚拟 IP、任务等端点，并改由业务层做重复检测。

## Goals

- 默认查询排除软删数据；删除接口改软删。
- 业务层重复校验：用户名/邮箱、虚拟 IP 名称等。

## Changes

- `stories.py`: 新增 `_not_deleted` 并用于故事查询、虚拟 IP 角色绑定校验。
- `virtual_ip.py`: `_not_deleted` 用于查询和重复校验，删除改为软删，列表默认排除软删。
- `tasks.py`: 任务查询/获取/更新/删除默认排除软删，删除改软删。
- `auth.py`: 注册/登录查询默认排除软删，用户名/邮箱重复校验落到业务层。

## Validation

- 未运行自动化测试（逻辑调整需后续 pytest 覆盖）。

## Next Steps

- 扩散软删过滤到剩余端点；结合前端切换 business_id；补测试。

## Linked Commits

- (pending)
