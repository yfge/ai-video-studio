---
id: 2026-07-16T12-35-00Z-canvas-v2-storyboard-planner
date: "2026-07-16T12:35:00Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - planner
  - clip-storyboard
  - timeline-placement
related_paths:
  - ai-pic-backend/app/services/production_canvas/planner_ports.py
  - ai-pic-backend/app/services/production_canvas/planner_contracts.py
  - ai-pic-backend/app/services/production_canvas/skill_planner.py
  - ai-pic-backend/app/services/production_canvas/render_execution.py
summary: Switch the canonical Production Canvas planner to the clip-storyboard v2 graph while retaining legacy v1 skills and ports for saved runs.
---

## User Prompt

采用故事板的形式，不用首尾帧了。按确认方案实现，并保持最小化颗粒度提交。

## Goals

- 将新建 Production Canvas 的规范图切换到 clip storyboard sheet。
- 视频候选只消费人工选用的 `approved_storyboard`，不连接 `start_frame`。
- 视频候选审核后通过独立 `timeline.place` 节点回填 stable `clip_id`。
- Render、Export 和 Report 只消费显式放置后的 Timeline 与交付证据。
- 保留旧 `storyboard.plan`、`image.candidates` 和首帧 binding，供历史 v1 运行恢复。

## Changes

- 将规范 Planner 图固定为
  `brief.compose -> content.plan -> asset.select -> script.generate -> timeline.assemble -> storyboard.candidates -> video.candidates -> timeline.place -> timeline.render -> timeline.export -> report.summarize`。
- 为 `timeline.assemble` 增加 `timeline_clip` 输出，为故事板候选增加
  `approved_storyboard` 选用输出。
- `video.candidates` 的规范 binding 改为整张故事板输入；规范边中不再出现
  `start_frame`。
- `timeline.place` 同时消费 stable clip 与已选视频，并输出 `placed_timeline` 给 Render。
- Export 增加 `delivery` execution ref，Report 通过显式边消费该证据。
- Planner catalog 只向自主规划器暴露 v2 规范技能；旧技能与 binding 继续留在注册表。
- 新建画布 manifest 版本升级为 `production_canvas.v2`。
- 将超限的 Production Canvas API 集成测试按完整测试函数机械拆分，保留旧
  `storyboard.plan` 执行兼容覆盖，并使两个测试文件都低于 250 行。

## Validation

- Focused Planner/API/Render suite:
  `pytest -q tests/unit/test_production_canvas_autonomous_planner.py tests/unit/test_production_canvas_skill_plan.py tests/unit/test_production_canvas_v2_planner_contract.py tests/unit/test_production_canvas_skill_registry.py tests/integration/test_production_canvas_api.py tests/integration/test_production_canvas_render_api.py tests/unit/test_production_canvas_storyboard_graph_runtime.py`
  - `22 passed`; `0 failed`.
- Full Production Canvas regression:
  `pytest -q tests/unit/test_production_canvas_*.py tests/integration/test_production_canvas_*.py`
  - `129 passed`; `0 failed`.
- Split API and legacy execution tests: `6 passed`; `0 failed`.
- Changed-file Ruff and `git diff --check`: passed.
- File-size checks: all changed backend service files remain below the 250-line hard limit.
- Clean-worktree `pre-commit run --files <planner paths>`: passed, including repository
  contracts and the full backend quick gate.

## Next Steps

- 在下一笔原子提交中对齐前端端口、模板、候选审核和显式 Timeline 放置控件。
- 最后更新设计文档与 `tasks.md`，并完成真实浏览器验证。

## Linked Commits

- This ledger is included in the canonical v2 planner commit created for this task.
