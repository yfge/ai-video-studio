---
id: 2026-01-26T14-10-00Z-script-quality-lint
date: 2026-01-26T14:10:00Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, tasks, scripts]
related_paths:
  - tasks.md
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/quality.py
  - ai-pic-backend/app/core/celery_app.py
  - ai-pic-backend/app/models/task.py
  - ai-pic-backend/app/schemas/script_quality.py
  - ai-pic-backend/app/services/script_quality/__init__.py
  - ai-pic-backend/app/services/script_quality/checks.py
  - ai-pic-backend/app/services/script_quality/constants.py
  - ai-pic-backend/app/services/script_quality/lint_engine.py
  - ai-pic-backend/app/services/script_quality/task_entrypoints.py
  - ai-pic-backend/app/services/script_quality/utils.py
  - ai-pic-backend/app/services/task_worker_script_quality.py
  - ai-pic-backend/alembic/versions/369390d31ba2_add_script_review_tasktype.py
  - ai-pic-backend/tests/test_script_quality_lint.py
  - ai-pic-frontend/src/components/features/tasks/taskTypeOptions.ts
summary: "Added deterministic script quality lint and script_review task flow"
---

## User Prompt

- 检查并更新 `tasks.md`，对照真实项目情况，确认现在可以开始哪些工作
- 任务体系补全：扩展后端 TaskType（story/episode/script/dialogue_audio/storyboard/video…）+ 前端 /tasks 支持 task_type 过滤
- 将“顶级漫剧剧本 26 条约束”落地为可执行的剧本质检/评分能力

## Goals

- 提供可审计、可复现的 deterministic 剧本质检（不依赖大模型）
- 将质检纳入任务体系：新增 `TaskType.script_review`，可在 /tasks 过滤查看
- 质检结果同时落到任务结果与脚本元数据，便于后续 UI/版本流衔接

## Changes

- Backend: 新增 `ScriptLint*` schemas（options/issues/metrics/result）
- Backend: 新增 `app/services/script_quality/`（规则检查、lint 编排、工具函数、Celery entrypoint）
- Backend: 新增 scripts 质检 API：
  - `POST /api/v1/scripts/{id}/quality-check`（同步）
  - `POST /api/v1/scripts/{id}/quality-check-async`（创建 Task + 交给 Celery）
- Backend: 扩展 `TaskType` 增加 `SCRIPT_REVIEW`，并补 alembic migration
- Backend: 新增 Celery task `tasks.script_quality_check`，并在 `celery_app` 显式 import 完成注册
- Backend: 修复 `script.extra_metadata` 写入（SQLAlchemy JSON 字段需 reassign，避免 in-place mutation 不落库）
- Frontend: `/tasks` 类型下拉新增 `script_review`（剧本质检）
- Tests: 新增 `ai-pic-backend/tests/test_script_quality_lint.py`

## Validation

- Backend (targeted): `pytest tests/test_script_quality_lint.py tests/test_tasks_minimal.py`
- Frontend: `npm run lint`（0 errors，warnings only）
- Backend (full): `pytest` 在当前环境存在大量既有失败（280 failed / 7 errors），本次变更新增用例通过且未引入新增失败类型
- Prod images: `./docker/build_prod_images.sh`（ok；IMAGE_TAG=8b38f22）
- Chrome E2E (localhost:8089):
  - 登录测试账号后，使用 `GET /api/v1/tasks?task_type=script_generation` 从既有任务解析得到 `script_id=110`
  - 触发 `POST /api/v1/scripts/110/quality-check-async` 创建 `script_review` 任务
  - 重启 `ai-video-celery-worker` 使 worker 注册新任务后，确认任务完成
  - 校验 `GET /api/v1/tasks/<id>` 含 `parameters.result`
  - 校验 `GET /api/v1/scripts/110` 含 `extra_metadata.script_quality`（task_id 对应）

## Next Steps

- 增加更多可自动检测的工业规则（动作四段式/平行任务/Turn 等），并保留不可判定项为人工/LLM review
- 在 Script 详情页增加“质检”入口与结果展示（issues/score/修订建议）
- 修复 `/api/v1/scripts` 列表查询在 MySQL 出现 `Out of sort memory (1038)` 的 500（索引/分页/字段裁剪）

## Linked Commits

- (pending) `feat(tasks): add script quality lint and script_review task`
