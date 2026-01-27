---
id: 2026-01-27T10-00-38Z-task-pipeline-audit-validation
date: 2026-01-27T10:00:38Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tasks, testing, docs]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories/async_tasks.py
  - ai-pic-backend/tests/fixtures/asyncio_loop.py
  - ai-pic-backend/tests/integration/test_task_pipeline_agent_run_audit.py
  - docs/TESTING_GUIDE.md
  - tasks.md
summary: "Added task pipeline integration coverage and documented /tasks audit checks"
---

## User Prompt

继续完成 P0：任务队列/可审计性补齐。

## Goals

- 为 Story/Episode/Script 异步任务补齐可验证的集成测试（Task 状态 + `parameters.agent_run` + 目标实体写入）。
- 补齐文档：记录 Celery 本地运行/调试与 `/tasks` 审计验证路径。
- 确保后端 pytest quick gate 可通过，并完成生产镜像构建验证。

## Changes

- 调整 `ai-pic-backend/app/api/v1/endpoints/stories/async_tasks.py`：将 `SessionLocal` 改为函数内导入，便于测试中 monkeypatch（与其它 async task 处理函数一致）。
- 新增 `ai-pic-backend/tests/integration/test_task_pipeline_agent_run_audit.py`：
  - 覆盖故事→剧集→剧本 `generate-async` 的 task 创建参数（task_type/parameters）；
  - 通过 patch `.delay` + 显式调用 Celery task `.run()`（避免在 FastAPI event loop 内执行 `anyio.run`）；
  - 校验 Task 状态、`parameters.agent_run.result_ref` 与 Story/Episode/Script `extra_metadata.agent_run` 落库。
- 更新 `ai-pic-backend/tests/fixtures/asyncio_loop.py`：将 `event_loop` fixture 由 session scope 改为 function scope，避免长跑用例中出现 async test 未 await 的不稳定问题。
- 更新 `docs/TESTING_GUIDE.md`：补充「任务队列与可审计性验证（/tasks + Celery）」章节（worker/beat 运行确认、Chrome 用例与验收点）。
- 更新 `tasks.md`：将“任务队列与 Agent 执行落库”的验证项标记为完成，并更新下一步清单。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `pytest -q ai-pic-backend/tests/integration/test_task_pipeline_agent_run_audit.py`
- `./docker/build_prod_images.sh`（镜像 tag 使用 `git rev-parse --short HEAD`，本次输出为 `38795ac`）

## Next Steps

- 生产环境分批执行 `ai-pic-backend/scripts/backfill_task_types.py`（建议先 `--dry-run`）。
- 补齐 dialogue-audio/timeline/storyboard/video 等任务在 Task 层的 `parameters.agent_run` 审计（与 story/episode/script 对齐）。

## Linked Commits

- TBD

