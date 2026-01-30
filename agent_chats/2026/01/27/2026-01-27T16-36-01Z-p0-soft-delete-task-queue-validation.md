---
id: 2026-01-27T16-36-01Z-p0-soft-delete-task-queue-validation
date: 2026-01-27T16:36:01Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, p0, soft-delete, tasks, audit]
related_paths:
  - ai-pic-backend/tests/scripts/test_script_regeneration_soft_delete.py
  - ai-pic-backend/tests/scripts/test_script_soft_delete_api.py
  - ai-pic-backend/tests/unit/test_virtual_ip_unique_name.py
  - tasks.md
summary: "Complete P0 validation for soft delete/regenerate + confirm task queue unified; add tests and verify via pytest, frontend lint, and Chrome E2E."
---

## User Prompt

把 P0 的都处理：补齐软删除验证（pytest + 前端 lint + Chrome E2E），并确认任务队列/审计闭环。

## Goals

- 为“全局软删除 + business_id”补齐可回归的 pytest 覆盖（软删、唯一性恢复、regenerate 新记录 + 旧记录软删）。
- 在真实浏览器链路验证：软删后列表/详情行为正确，regenerate 创建新记录并隐藏旧记录。
- 看板上把已完成的 P0 勾选项同步为真实状态。

## Changes

- 测试：\n+ - `ai-pic-backend/tests/scripts/test_script_regeneration_soft_delete.py`：覆盖 script regenerate task 会创建新 script 并软删旧 script，同时回写 Task `result_file_path`。\n+ - `ai-pic-backend/tests/scripts/test_script_soft_delete_api.py`：覆盖 script 软删后列表不返回、详情 404。\n+ - `ai-pic-backend/tests/unit/test_virtual_ip_unique_name.py`：新增用例覆盖 VirtualIP 软删后允许同名再次创建（唯一性按 `is_deleted` 维度恢复）。\n+- 看板：\n+ - `tasks.md`：勾选完成“软删验证”与“任务统一到 Task 队列”的 P0 项。

## Validation

- Pytest（pre-commit quick gate）：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（`849 passed, 1 skipped`）。
- Frontend lint：`cd ai-pic-frontend && npm run lint`（0 errors；若干 warnings，不影响通过）。
- Chrome E2E（真实链路）：\n+ - 登录 `geyunfei`（`http://localhost:8089/login`）。\n+ - 选择最新 script（`GET /api/v1/scripts?limit=1` 得到 `script_id=110`）。\n+ - 触发 regenerate：`POST /api/v1/scripts/110/regenerate` → `task_id=5852`。\n+ - 轮询 `GET /api/v1/tasks/5852` 直到 `completed`，返回 `result_file_path=script:112`。\n+ - 验证软删与可见性：\n+ - `GET /api/v1/scripts/110` → 404（旧 script 隐藏）。\n+ - `GET /api/v1/scripts/112` → 200（新 script 可用）。\n+ - `GET /api/v1/scripts?limit=20`：列表包含 `112` 不包含 `110`。\n+

## Next Steps

- P1：推进分镜 LangGraph 管线统一（规划+生成+审计轨迹落库）与前端 storyboard page 超大文件拆分。

## Linked Commits

- (current) 同提交。
