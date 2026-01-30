---
id: 2026-01-27T18-21-39Z-backfill-task-agent-run
date: 2026-01-27T18:21:39Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, p0, tasks, audit, scripts]
related_paths:
  - ai-pic-backend/scripts/backfill_task_agent_runs.py
  - tasks.md
summary: "Add production-safe backfill script for Task.parameters.agent_run (including FAILED/CANCELLED error context) and document it in tasks.md."
---

## User Prompt

还是补齐其它 task_type 的 agent_run 落库：生产执行历史任务回填（先 --dry-run，按 user/时间分批），并把 FAILED/CANCELLED 的 error context 写入 parameters.agent_run，形成审计闭环。

## Goals

- 提供一个可控的“历史任务 agent_run 回填”脚本：默认 dry-run，支持按 user/时间/ID 范围分批执行。
- 覆盖 FAILED/CANCELLED：即使 build_agent_run 为空也要写入 error context，方便在 `/tasks` 直接审计失败原因。

## Changes

- `ai-pic-backend/scripts/backfill_task_agent_runs.py`：新增回填脚本（两段模式：dry-run 统计/采样；`--apply` 执行写入）。\n+ - 默认仅处理 terminal 状态：`completed/failed/cancelled`。\n+ - 仅处理缺失/为空的 `parameters.agent_run`。\n+ - 通过 `task_type → kind` 映射调用 `persist_task_agent_run(...)`，FAILED/CANCELLED 自动补充 `error_message` 等审计信息。\n+ - 支持 `--user-id`、`--after/--before`、`--min-id/--max-id`、`--max-updates` 限流。
- `tasks.md`：在“任务队列与 Agent 执行落库”章节补充回填脚本与生产执行项。

## Validation

- 脚本 dry-run（容器内，能连到 `ai-video-mysql`）：\n+ - `docker exec ai-video-backend python /app/ai-pic-backend/scripts/backfill_task_agent_runs.py --show-samples 3`。\n+ - 输出样例包含 FAILED/COMPLETED task（证明可扫描到缺失 agent_run 的历史任务）。\n+ - 由于宿主机无法直连容器内 MySQL（`ai-video-mysql` 未映射端口），宿主机直接运行会报连接拒绝；生产建议在 backend 容器内执行或确保 DB 可达。
- 小范围 apply 校验（仅 1 条）：\n+ - `docker exec ai-video-backend python /app/ai-pic-backend/scripts/backfill_task_agent_runs.py --min-id 1 --max-id 1 --apply --max-updates 5 --show-samples 0`。\n+ - Chrome（登录 `geyunfei`）校验：`GET /api/v1/tasks/1` → 200，且 `parameters.agent_run.task_status=failed` 并包含 `error.message`（审计闭环）。

## Next Steps

- 生产：先用 `--dry-run --user-id <id> --after/--before` 确认待回填数量，再分批 `--apply`，每批配合 `--max-updates` 控制写入量。

## Linked Commits

- (current) 同提交。
