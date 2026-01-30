---
id: 2026-01-27T17-43-51Z-fix-scoring-endpoints
date: 2026-01-27T17:43:51Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, scoring, microgenre, fix]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scoring.py
  - ai-pic-backend/app/services/scoring/script_score_service.py
  - ai-pic-backend/app/services/scoring/traffic_sheet_service.py
  - ai-pic-backend/tests/fixtures/mock_ai_service.py
  - ai-pic-backend/tests/unit/services/scoring/test_script_score_service.py
  - ai-pic-backend/tests/unit/services/scoring/test_traffic_sheet_service.py
  - ai-pic-backend/tests/unit/test_scoring_endpoints_from_db.py
  - tasks.md
summary: "Fix scoring endpoints to use ai_manager + current DB fields; add endpoint tests and verify via pytest, Docker prod build, and Chrome E2E."
---

## User Prompt

继续完成 P0/P1 任务：把可审计性与投流闭环相关能力补齐，并把能立即落地的后端问题先修好。

## Goals

- 修复 `/api/v1/scoring/score/{script_id}` 与 `/api/v1/scoring/traffic-sheet/{script_id}` 的运行错误，确保可以从 DB 加载脚本并稳定生成评分/投流表。
- 统一改为走 `ai_manager.generate_text`（返回 `AIResponse`），并保持可 monkeypatch 以便测试。
- 补齐/修正单测覆盖，防止回归。

## Changes

- `ai-pic-backend/app/api/v1/endpoints/scoring.py`：移除错误的 `AIService(db)` 实例化，改为使用全局 `ai_service`（运行时导入，便于测试 monkeypatch）。
- `ai-pic-backend/app/services/scoring/script_score_service.py`：统一走 `ai_manager.generate_text` + `ScriptScoreResult` 的 JSON schema；兼容 `AIResponse.data` 为 dict 或 str。
- `ai-pic-backend/app/services/scoring/traffic_sheet_service.py`：统一走 `ai_manager.generate_text` + `TrafficSheet` 的 JSON schema；兼容 `AIResponse.data` 为 dict 或 str。
- `ai-pic-backend/tests/fixtures/mock_ai_service.py`：扩展 mock ai_manager 的 `generate_text`，按 prompt 返回评分/投流表结构化 payload。
- 测试：
  - `ai-pic-backend/tests/unit/test_scoring_endpoints_from_db.py`：新增 endpoint 覆盖（score/traffic-sheet from DB）。
  - `ai-pic-backend/tests/unit/services/scoring/test_script_score_service.py` 与 `ai-pic-backend/tests/unit/services/scoring/test_traffic_sheet_service.py`：更新 mock 形状为 `ai_service.ai_manager.generate_text`（AsyncMock + AIResponse）。
- 看板：
  - `tasks.md`：补充勾选项，记录 scoring endpoints 修复完成。

## Validation

- Pytest：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（`850 passed, 1 skipped`）。
- Docker：`./docker/build_prod_images.sh`（backend/frontend 镜像均 build + push 成功）。
- Chrome E2E（真实链路）：登录 `geyunfei`（`http://localhost:8089/login`），对 `script_id=112` 调用：
  - `GET /api/v1/scoring/score/112` → 200，返回 `overall_score`/`dimension_scores` 等字段。
  - `GET /api/v1/scoring/traffic-sheet/112` → 200，返回 `assets` 且长度 > 0。

## Next Steps

- P1：把 HookScore/ScriptScore 结果写入 Task `parameters.agent_run`（含低分修订建议），并打通“微类型→故事/剧集/剧本→投流表→分镜/时间线标注”Chrome E2E。
- P0：复核并修复 `/api/v1/scripts` 列表在 MySQL 上的 `Out of sort memory (1038)`（若线上仍复现则回滚看板勾选并补回归）。

## Linked Commits

- (current) 同提交。
