---
id: 2025-12-13T11-44-35Z-style-spec-schema-api
date: 2025-12-13T11:44:35Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, styles, schema]
related_paths:
  - ai-pic-backend/app/schemas/style.py
  - ai-pic-backend/app/utils/style_utils.py
  - ai-pic-backend/app/api/v1/endpoints/styles.py
  - ai-pic-backend/app/api/v1/api.py
summary: "Introduce StyleSpec schema + code-defined presets and expose them via API."
---

## User Prompt

实现“漫剧绘画风格”13 维枚举，后端作为唯一真源提供 schema/preset；前端后续可按不同页面只传部分字段，由后端填充。

## Goals

- 定义可落库/可透传的 `StyleSpec`（13 维枚举，允许 partial override）。
- 提供 API 给前端拉取 schema 与 preset（预设写死在代码里，全局统一）。

## Changes

- Added `StyleSpec` + 13-dim enums and API response models in `ai-pic-backend/app/schemas/style.py`.
- Added code-defined presets/defaults and resolver helpers in `ai-pic-backend/app/utils/style_utils.py`.
- Added new endpoints `GET /api/v1/styles/schema` and `GET /api/v1/styles/presets` in `ai-pic-backend/app/api/v1/endpoints/styles.py`.
- Registered the new router in `ai-pic-backend/app/api/v1/api.py`.

## Validation

- `cd ai-pic-backend && ruff check app/api/v1/endpoints/styles.py app/schemas/style.py app/utils/style_utils.py`
- `cd ai-pic-backend && black --check app/api/v1/endpoints/styles.py app/schemas/style.py app/utils/style_utils.py`

## Next Steps

- Wire `style_spec` / `style_preset_id` into all txt2img/img2img endpoints + Celery payloads, and persist resolved spec into metadata.
- Update frontend to fetch presets/schema from backend and replace legacy `style` dropdowns with a shared selector.

## Linked Commits

- feat(backend): add style spec schema endpoints
