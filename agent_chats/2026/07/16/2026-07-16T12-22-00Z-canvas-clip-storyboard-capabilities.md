---
id: 2026-07-16T12-22-00Z-canvas-clip-storyboard-capabilities
date: "2026-07-16T12:22:00Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - clip-storyboard
  - video-candidates
  - timeline-placement
related_paths:
  - ai-pic-backend/app/services/production_canvas/clip_media_execution.py
  - ai-pic-backend/app/services/production_canvas/placement_execution.py
  - ai-pic-backend/app/services/production_canvas/storyboard_candidates.py
  - ai-pic-backend/app/services/production_canvas/executor.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py
  - ai-pic-backend/app/schemas/timeline.py
summary: Add clip storyboard review, storyboard-driven video candidates without keyframes, and an executable Timeline placement node while preserving the legacy v1 path.
---

## User Prompt

采用故事板的形式，不用首尾帧了。按确认方案实现，并保持最小化颗粒度提交。

## Goals

- 复用现有 clip-scoped 2/4/6/9 格故事板生成，不复制 provider 或 worker 逻辑。
- 让视频候选消费人工选用的整张 clip storyboard sheet，不使用首帧或尾帧。
- 视频候选生成后先停在人工审核，不提前触发 Timeline render。
- 将审核后回填 stable `clip_id` 暴露为可执行 `timeline.place` 节点。
- 保留旧 `storyboard.plan -> image.candidates -> video.candidates` v1 能力，后续提交再切换默认 Planner 图。

## Changes

- 新增 `storyboard.candidates` 执行器，复用
  `GridStoryboardSheetService.queue_clip_sheet`，按现有规则自动选择 2/4/6/9 格。
- 新增 clip storyboard 视频候选执行器，复用
  `TimelineClipVideoReworkQueueService`，固定
  `reference_mode=clip_storyboard_sheet`、`use_clip_storyboard=true`、
  `use_end_frame=false`、`return_last_frame=false` 和 `auto_render=false`。
- 为 Timeline clip video rework 请求增加向后兼容的 `auto_render` 开关；旧 API 默认值仍为
  `true`。
- 将 clip storyboard sheet 暴露为可审核图片候选，输出 `approved_storyboard`；该模式只
  展示当前 clip 的最新 sheet，避免审核结果与 Timeline 当前 storyboard ref 分叉。
- 新增 `timeline.place` 图执行器，复用既有显式 placement 服务，将已选视频写入 stable
  `clip_id` 并返回新 Timeline version。
- 图运行时新增 `timeline_clip`、`placed_timeline` 和 `approved_storyboard` 输入解析。
- storyboard-sheet 视频模式禁用候选分支，避免把视频候选误当成新的图片参考输入。
- 新能力已登记到 Skill registry，但本提交不改变默认 v1 Planner 图。

## Validation

- Production Canvas focused suite:
  `pytest -q tests/unit/test_production_canvas_skill_registry.py tests/unit/test_production_canvas_storyboard_graph_runtime.py tests/integration/test_production_canvas_clip_storyboard_api.py tests/integration/test_production_canvas_timeline_place_node_api.py tests/integration/test_production_canvas_timeline_placement_api.py tests/integration/test_production_canvas_candidate_review_api.py tests/integration/test_production_canvas_media_api.py tests/unit/test_production_canvas_graph_runtime.py`
  - `14 passed`; `0 failed`.
- Existing Timeline storyboard and rework regression:
  `pytest -q tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_video_sheet_sequence_api.py tests/test_timeline_clip_video_rework_render_queue.py tests/test_timeline_storyboard_grid_api.py tests/test_timeline_storyboard_grid_processor.py`
  - `15 passed`; `0 failed`.
- Changed-file Ruff and `git diff --check`: passed.
- File-size checks: changed backend service files remain within repository hard limits; shared
  `timeline.py` schema remains exactly 250 lines.
- Repository quick wrapper could not enter pytest because it attempted to install pinned test
  dependencies from PyPI and the sandbox could not resolve the package index. Direct focused and
  regression pytest runs above used the existing environment and passed.
- Clean-worktree `pre-commit run --files <capability paths>`: passed, including repository
  contracts and the full backend quick gate.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` was attempted in the
  clean worktree. The Docker classic builder produced no progress after entering backend image
  packaging and was interrupted; the final diagnostic showed its `.codex` tar stream closing after
  interruption, not a source compile failure.

## Next Steps

- In the next atomic commit, switch the canonical Planner/compiler graph and manifest to
  `production_canvas.v2`.
- Then align frontend ports, templates, candidate controls, and explicit Timeline placement UI.
- Finish with source-of-truth docs, full backend/frontend gates, and real browser validation.

## Linked Commits

- This ledger is included in the capability commit created for this task.
