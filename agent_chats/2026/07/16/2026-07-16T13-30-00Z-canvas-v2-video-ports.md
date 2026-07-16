---
id: 2026-07-16T13-30-00Z-canvas-v2-video-ports
date: "2026-07-16T13:30:00Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - clip-storyboard
  - typed-ports
  - legacy-restore
related_paths:
  - ai-pic-backend/app/services/production_canvas/planner_ports.py
  - ai-pic-backend/app/services/production_canvas/nodes.py
  - ai-pic-frontend/src/components/features/canvas/productionCanvasPorts.ts
summary: Version Production Canvas video ports so v2 requires one approved storyboard while restored v1 runs retain their start-frame input.
---

## User Prompt

采用故事板的形式，不用首尾帧了。按确认方案实现，并保持最小化颗粒度提交。

## Goals

- 新建 `production_canvas.v2` 的 Video 节点只接收整张已选用故事板。
- 不在 v2 UI 或编译图中暴露首帧、尾帧端口。
- 旧 `production_canvas.v1` Run 继续按原保存语义恢复 `start_frame`。

## Changes

- 节点端口构建新增 manifest version 输入；v2 的 `video.candidates` 只返回必选
  `approved_storyboard`，默认和 v1 仍返回 legacy 端口。
- 新计划、规范图校验和 Run 恢复都显式传递 manifest version。
- 前端 Video 默认端口改为必选 `approved_storyboard`；服务端显式提供的 legacy
  `start_frame` 端口仍原样保留。
- 增加 API、planner、Run 恢复和前端 typed-port 回归断言。

## Validation

- `cd ai-pic-backend && python -m pytest -q tests/unit/test_production_canvas*.py tests/integration/test_production_canvas*.py`
  - `129 passed`; `0 failed`.
- `cd ai-pic-frontend && ./node_modules/.bin/tsx --test tests/productionCanvasPorts.test.ts`
  - focused typed-port tests passed.
- `git diff --check`
  - passed.

## Next Steps

- 修复浏览器验证发现的 planned-edge 重复追加警告。
- 重跑 Production Canvas v2 真实浏览器链路并记录无首尾帧端口证据。

## Linked Commits

- This ledger is included in the versioned video-port fix commit created for this task.
