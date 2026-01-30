---
id: 2025-10-20T07-10-00Z-story-structure-schemas-services
date: 2025-10-20T07:10:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, schemas, services]
related_paths:
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/app/services/story_structure_service.py
summary: "Add Pydantic schemas and service layer for normalized story structure CRUD."
---

## User Prompt

继续按计划推进，补充 Schemas 与 Service，为后续 API 最小集成铺路。

## Goals

- 定义与 ORM 对应的 Pydantic 输入/输出模型，支持 `from_attributes`。
- 提供最小服务层：按 story/script/scene 读取，支持基本创建操作。

## Changes

- 新增 `app/schemas/story_structure.py`：定义 Treatment/StepOutline/Scene/SceneBeat/Shot 的 Create/Response 模型。
- 新增 `app/services/story_structure_service.py`：实现列表与创建的基础函数。

## Validation

- 静态校对字段与 ORM 一致性；方法签名与调用语义明确。
- 将在 API 接入与后续测试中进一步验证。

## Next Steps

- 提供最小读写 API：列出脚本下 scenes、列出 scene 下 shots、创建 treatment 等。
- 在前端分镜页试点读取（以开关方式）。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）
