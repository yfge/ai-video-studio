---
id: 2025-12-17T04-37-50Z-frontend-business-id-backend-support
date: 2025-12-17T04:37:50Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, schema]
related_paths:
  - ai-pic-backend/app/schemas/script.py
  - ai-pic-backend/app/schemas/virtual_ip.py
  - ai-pic-backend/app/schemas/task.py
  - ai-pic-backend/app/schemas/image.py
  - ai-pic-backend/app/schemas/user.py
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/app/api/v1/endpoints/tasks.py
summary: "Expose business_id fields in backend responses to enable frontend routing"
---

## User Prompt

- “前端切换业务主键 business_id，适配再生成返回的新记录”。

## Goals

- 后端响应暴露 `business_id`（及关联业务键），便于前端使用业务主键。

## Changes

- Schemas: Story/Episode/Script responses now include `business_id` + parent business ids; VirtualIP/VirtualIPImage include `business_id`/`virtual_ip_business_id`; Task includes `business_id`/`target_business_id`; Image/User add `business_id`; Story structure responses include business ids for treatments/step outlines/scenes/beats/shots.
- Tasks endpoint serializer now returns `business_id` and `target_business_id`.

## Validation

- 未运行自动化测试（schema-only change）。

## Next Steps

- 前端改用 `business_id` 路由/再生成跳转；可补测试验证字段透传。

## Linked Commits

- (pending)
