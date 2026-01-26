---
id: 2026-01-26T09-55-37Z-backfill-task-types
date: 2026-01-26T09:55:37Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tasks]
related_paths:
  - ai-pic-backend/scripts/backfill_task_types.py
  - tasks.md
summary: "Add one-off script to backfill legacy Task.task_type values"
---

## User Prompt

- 选择任务 1：历史 TaskType 回填。

## Goals

- 提供可控、可审计的一次性回填方案，把历史 `Task.task_type=IMAGE_GENERATION` 但实际属于 story/episode/script/dialogue_audio/timeline/storyboard/video/text 的任务纠正为正确类型。
- 默认 dry-run，避免误操作；支持按 user/时间范围分批。

## Changes

- 新增 `ai-pic-backend/scripts/backfill_task_types.py`：
  - 仅针对 `task_type=IMAGE_GENERATION` 的记录
  - 按 title/prompt 规则匹配并更新为正确 `TaskType`
  - 默认 dry-run；`--apply` 才会执行更新
  - 支持 `--user-id` / `--after` / `--before` 分批
- 更新 `tasks.md`：在“任务队列与 Agent 执行落库”补充回填脚本与生产执行事项。

## Validation

- Dev DB (docker):
  - `docker exec ai-video-backend python scripts/backfill_task_types.py --user-id 1 --show-unmatched 5`（dry-run 输出各类型待更新数量）
  - `docker exec ai-video-backend python scripts/backfill_task_types.py --apply --user-id 1 --show-unmatched 5`（执行更新，剩余 IMAGE_GENERATION=285）
- Prod images: `./docker/build_prod_images.sh`（ok；IMAGE_TAG=cbde43d）
- Chrome (MCP):
  - `http://localhost:8089/login` 登录 `geyunfei`
  - 进入 `/tasks` 点击“刷新”，确认历史任务的类型从“图像生成（image_generation）”更新为对应类型（例如“生成剧本”→`script_generation`，“一键时间轴流水线”→`timeline_pipeline`）

## Next Steps

- 在生产环境按窗口期执行回填（建议先 dry-run，再按时间范围分批），并抽样校验 `/tasks` 过滤结果。
- 如发现未覆盖的 title/prompt 模式，补充规则并记录迁移策略。

## Linked Commits

- (pending)
