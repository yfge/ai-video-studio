---
id: 2025-12-07T09-40-00Z-environment-api
date: 2025-12-07T09:40:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, migration, story-structure]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/app/models/story_structure.py
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/alembic/versions/e2f4c6d8b9aa_add_character_ids_to_shots.py
summary: "Add environment CRUD endpoints, bind scenes to environments, and allow shots to carry character IDs"
---

## User Prompt

- 实现环境资产 CRUD 与场景绑定 API（场景/分镜帧携带 environment_id & character_ids）。

## Goals

- 提供环境资产的增删改查接口。
- 场景创建/更新时校验并绑定 environment_id；分镜帧（shots）支持记录参与角色 ID。
- 数据层补充所需字段和迁移。

## Changes

- 模型/Schema：`Scene` 增加 `environment_id` 关联；新增 `Environment` 模型；`Shot` 增加 `character_ids` JSON 字段，对应 Pydantic Create/Update/Response 更新。
- 服务层：场景创建/更新校验环境存在；补充环境 CRUD 服务；更新 shot 更新逻辑；创建场景批量时校验环境。
- API：`story_structure` 路由新增环境列表/查询/创建/更新/删除；场景更新/创建对环境不存在返回 404。
- 迁移：`e2f4c6d8b9aa_add_character_ids_to_shots` 为 shots 添加 `character_ids` 列。

## Validation

- 未跑自动测试；需在后端环境执行 `alembic upgrade head` 应用新列后再验证。
- 手工检查 API 路由加载无语法错误，场景创建/更新时若 environment_id 不存在会返回 404。

## Next Steps

- 前端环境管理 UI 与场景/分镜环境选择器；图像/视频生成链路注入环境与角色参考图。

## Linked Commits

- (pending)
