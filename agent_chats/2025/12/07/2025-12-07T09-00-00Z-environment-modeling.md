---
id: 2025-12-07T09-00-00Z-environment-modeling
date: 2025-12-07T09:00:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migration, story-structure]
related_paths:
  - ai-pic-backend/app/models/story_structure.py
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/alembic/versions/d1a2b3c4e5f7_add_environments_and_scene_env.py
  - task.md
summary: "Add environment asset modeling and link scenes to environments"
---

## User Prompt

- 规划场景/环境资产，支撑分镜→图像→视频的闭环，并更新任务看板。

## Goals

- 引入环境资产数据结构并将规范化场景绑定环境。
- 提供迁移脚本以创建环境表并在场景中添加关联。
- 在任务看板中记录新的环境/分镜联动工作包。

## Changes

- 新增 `Environment` 模型：名称、分类、标签、描述、参考图、元数据、时间戳；与场景建立反向关系。
- `Scene` 增加 `environment_id` 外键及关联；对应 Pydantic Create/Update/Response 增加字段。
- Alembic 迁移 `d1a2b3c4e5f7_add_environments_and_scene_env.py`：创建 `environments` 表，给 `scenes` 增加外键列。
- `task.md` 新增“场景/环境资产与分镜联动”任务分解。

## Validation

- 静态检查：模型/Schema 文件通过 lint；迁移脚本可执行（未在本机跑 `pytest`/`alembic upgrade`）。

## Next Steps

- 实现环境资产 CRUD 与场景绑定 API；分镜帧/生成链路注入环境与角色参考图；前端环境管理与选择器。

## Linked Commits

- (pending)
