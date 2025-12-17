---
id: 2025-12-17T04-05-16Z-soft-delete-filters-round3
date: 2025-12-17T04:05:16Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/api/v1/endpoints/images.py
  - ai-pic-backend/app/api/v1/endpoints/users.py
summary: "Extended soft-delete filtering to images/virtual IP images/users and aligned deletes to soft delete"
---

## User Prompt

- 继续将软删过滤扩展到剩余端点，并保持删除行为为软删但对前端保持原语义。

## Goals

- 默认查询排除软删数据，删除接口改软删。
- 业务层重复校验仍在服务层完成。

## Changes

- `virtual_ip_images.py`: 添加 `_not_deleted`，虚拟 IP 归属校验过滤软删；图像查询/默认图像更新/删除改为软删。
- `images.py`: 列表/详情过滤软删。
- `users.py`: 列表/详情/更新过滤软删，删除改软删（前端提示保持“用户已删除”）。

## Validation

- 未跑自动化测试（需后续覆盖）。

## Next Steps

- 将软删过滤补到其他端点（story_structure 等），前端切换 business_id，补测试。

## Linked Commits

- (pending)
