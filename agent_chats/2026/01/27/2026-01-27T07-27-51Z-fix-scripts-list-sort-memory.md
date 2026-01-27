---
id: 2026-01-27T07-27-51Z-fix-scripts-list-sort-memory
date: 2026-01-27T07:27:51Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, api, scripts]
related_paths:
  - tasks.md
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/schemas/script.py
  - ai-pic-backend/tests/test_scripts_list_lite.py
summary: "Fix /api/v1/scripts 500 by returning lite list items and avoiding MySQL sort buffer exhaustion"
---

## User Prompt

- 先修复 `/api/v1/scripts` 列表 MySQL `Out of sort memory (1038)`（`tasks.md:47`）

## Goals

- 让 `/api/v1/scripts?limit=...` 在真实 MySQL 数据量下不再 500
- 降低 scripts 列表接口的 DB 负载与响应体大小（列表只返回必要字段）

## Changes

- Backend: 新增 `ScriptListItemResponse`（列表轻量返回，不含 content/scenes/dialogues/stage_directions）
- Backend: scripts 列表相关 endpoints 改为：
  - `load_only(...)` 只查询必要列（避免排序/临时表包含大文本/JSON）
  - `ORDER BY scripts.id DESC`（使用主键索引，避免 MySQL sort buffer 耗尽）
- Tests: 新增 `test_scripts_list_lite.py`，验证列表响应为 lite（不包含 `content` 字段）
- Board: `tasks.md` 标记该 fix 已完成

## Validation

- Backend: `cd ai-pic-backend && pytest tests/test_scripts_list_lite.py tests/test_tasks_minimal.py`
- Chrome (MCP):
  - 登录 `http://localhost:8089/login`（`geyunfei`）
  - 调用 `GET /api/v1/scripts?limit=5` 从 500 恢复为 200，并确认返回字段为 lite
- Prod images: `./docker/build_prod_images.sh`（ok；IMAGE_TAG=f800b7d）

## Next Steps

- 如需按 `created_at` 精确排序 + 更大分页，补充索引与 keyset pagination（基于 `(id)` 或 `(created_at, id)`）

## Linked Commits

- (pending)
