---
id: 2025-12-07T10-05-00Z-environment-front-api
date: 2025-12-07T10:05:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, env-assets]
related_paths:
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-frontend/src/utils/api.ts
summary: "Prepare environment and character plumbing for storyboard plan and add frontend env API client"
---

## User Prompt

- 继续完成场景相关工作：让分镜规划可携带环境/角色信息，前端提供环境接口。

## Goals

- 后端分镜规划 schema 支持 environment_id、character_ids。
- 前端 API 客户端增加环境资产 CRUD 接口定义。

## Changes

- `ai-pic-backend/app/schemas/generation.py`: StoryboardPlanScene 增加 `environment_id`、`character_ids` 字段，便于后续生成链路注入环境/角色。
- `ai-pic-frontend/src/utils/api.ts`: 新增 Environment 类型与 CRUD 方法（list/create/update/delete），以便后续环境管理页调用。

## Validation

- 静态检查：TS/py 文件语法正常；未跑自动测试。

## Next Steps

- 前端实现环境管理页面与场景/分镜环境选择器；后端生成链路消费 environment_id/character_ids。

## Linked Commits

- (pending)
