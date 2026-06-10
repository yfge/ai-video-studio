---
id: 2026-06-10T13-30-00Z-workbench-timeline-ready-fix
date: "2026-06-10T13:30:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - backend
  - workbench
  - bugfix
related_paths:
  - ai-pic-backend/app/services/workbench_service.py
  - ai-pic-backend/tests/integration/test_workbench_summary_api.py
summary: workbench「时间轴就绪」只读 Timeline 表，删除 episode.extra_metadata.audio_timeline 旧回退——timeline 删除后 dashboard 不再误报就绪。
---

# Workbench Timeline-Ready Reads Timeline Table Only

## User Prompt

生产链路优化 Phase B1：dashboard「继续制作」表的 timeline_ready 在查 Timeline 表之外还回退到 episode.extra_metadata['audio_timeline']（流水线重建/删除 timeline 后不更新），导致状态误报。

## Goals

- `timeline_ready` 仅由 Timeline 表行（未删除）决定。
- 审计 `_storyboard_ready`：其读取 `script.extra_metadata['storyboard'].frames`，与前端 `useEpisodeMetadata` 的 selectedStoryboard 同源一致，不属过期路径，保留。
- 测试覆盖"只有旧 metadata、无 Timeline 行 → 不就绪"。

## Changes

- `workbench_service.py`：删除 `_timeline_ready()` 旧 metadata 回退函数；`timeline_ready = _timeline_row_ready(timeline)`，并在 helper 上注明 Timeline 表为唯一事实来源。
- 测试：`test_workbench_summary_aggregates_user_state` 场景补建真实 Timeline 行（原来靠脏 metadata 通过）；新增 `test_workbench_summary_ignores_stale_audio_timeline_metadata` 断言旧 metadata 不再算就绪且 timeline_id 为空。

## Validation

- `python -m pytest tests/integration/test_workbench_summary_api.py -q`：4 passed。
- `python run_tests.py quick` 因依赖解析环境问题无法启动（ResolutionImpossible，与本改动无关）；以 pytest 直跑该 API 全部集成测试代替。

## Next Steps

- B2：暴露自动创建角色。

## Linked Commits

- This commit.
