---
id: 2026-01-27T18-44-43Z-script-generation-scoring-artifacts
date: 2026-01-27T18:44:43Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, p1, scoring, tasks, audit]
related_paths:
  - ai-pic-backend/app/services/scoring/artifacts.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/tests/integration/test_task_pipeline_agent_run_audit.py
  - tasks.md
summary: "Generate ScriptScore + TrafficSheet during script generate/regenerate and persist into Script.extra_metadata + Task.parameters.agent_run for auditability."
---

## User Prompt

继续完成 P1：把评分报告/投流表/素材标签在任务层可审计化；把 HookScore/ScriptScore 接入生成链路，并在前端任务页可直接查看。

## Goals

- 在脚本生成/再生成任务中自动生成 `ScriptScore` 与 `TrafficSheet`，并派生素材标签（hook_types/durations 等）。
- 将结果写入 `Script.extra_metadata.scoring` 与 `Task.parameters.agent_run`，实现“任务层审计闭环”（无需跳转脚本详情或日志）。

## Changes

- `ai-pic-backend/app/services/scoring/artifacts.py`：新增 scoring pipeline（生成 score + traffic_sheet + asset_tags 的统一入口）。
- `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`：在 `_process_script_generation_task` / `_process_script_regeneration_task` 中：
  - 当存在 marketing meta（market_region/micro_genre/hook_plan 等）时，生成 scoring artifacts；
  - 写入 `extra_metadata.scoring`，并合并进 `extra_metadata.agent_run.scoring`（Task agent_run 会自动继承）。
- `ai-pic-backend/tests/integration/test_task_pipeline_agent_run_audit.py`：脚本生成用例补充 market/micro_genre，并断言 Task agent_run 含 `scoring.script_score/traffic_sheet/asset_tags`。
- `tasks.md`：勾选完成“接入生成链路/写入 Task agent_run”两项。

## Validation

- Pytest（quick gate）：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（`850 passed, 1 skipped`）。
- Pytest（integration）：`cd ai-pic-backend && pytest tests/integration/test_task_pipeline_agent_run_audit.py -vv`（1 passed）。
- Docker：`./docker/build_prod_images.sh`（backend/frontend 镜像均 build + push 成功）。
- Chrome E2E（真实链路）：登录 `geyunfei`（`http://localhost:8089/login`）：\n+  - `POST /api/v1/scripts/generate-async`（episode_id=124，带 market_region/micro_genre）→ `task_id=5853`。\n+  - 轮询 `GET /api/v1/tasks/5853` 直到 `completed`，返回 `result_file_path=script:113`。\n+  - 验证 `GET /api/v1/tasks/5853` 的 `parameters.agent_run.scoring` 存在，且包含 `script_score` 与 `traffic_sheet`。

## Next Steps

- 验证：补齐“选择微类型→生成故事/剧集/剧本→投流表→分镜/时间线标注”的完整 Chrome E2E 记录（tasks.md:85）。
- 若需要自动低分重写：在 `verdict=review/rewrite` 时加入可控的二次修订开关（避免默认增加成本与失败率）。

## Linked Commits

- (current) 同提交。

