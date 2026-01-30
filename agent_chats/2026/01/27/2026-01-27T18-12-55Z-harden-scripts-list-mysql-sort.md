---
id: 2026-01-27T18-12-55Z-harden-scripts-list-mysql-sort
date: 2026-01-27T18:12:55Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, fix, mysql, scripts]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - tasks.md
summary: "Harden /api/v1/scripts list query to reduce MySQL sort buffer (1038) risk by paging IDs first, then loading lite fields."
---

## User Prompt

先修复 `/api/v1/scripts` 列表在 MySQL 上偶发 `Out of sort memory (1038)` 的 500（看板已登记）。

## Goals

- 让 `/api/v1/scripts` 列表查询在 MySQL 上更稳定，避免 join/filter 下触发 filesort 导致 sort buffer 1038。
- 保持返回结构为 lite 列表项（不返回 `content/scenes/dialogues`）。

## Changes

- `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`：将脚本列表改为两段查询：
  - 第一段仅选取 `Script.id` 并按 `id DESC` 分页（最小化 filesort 内存占用）。
  - 第二段按这些 `id` 回查 `load_only` 的列表字段并按 `id DESC` 返回。
- `tasks.md`：补充“进一步加固”勾选项说明。

## Validation

- Pytest：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（`850 passed, 1 skipped`）。
- Docker：`./docker/build_prod_images.sh`（backend/frontend 镜像均 build + push 成功）。
- Chrome E2E（真实链路）：登录 `geyunfei`（`http://localhost:8089/login`），调用 `GET /api/v1/scripts?limit=5` → 200，返回 `id` 倒序且不含 `content` 字段。

## Next Steps

- 若线上仍复现 1038：收集 EXPLAIN/慢查询日志（含 sort_buffer_size 与执行计划），再进一步做 keyset pagination（基于 `before_id`）替代大 offset。

## Linked Commits

- (current) 同提交。
