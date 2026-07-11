## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交；先提交现有变更。

## Goals

- 修复已有 Timeline 场景下 Video Candidates 因缺少稳定 clip 映射而阻塞的问题。
- 保持 Timeline 为事实来源，不放宽视频队列的输入校验，也不重复调用 provider 规划。

## Changes

- Timeline Skill 检测并复用当前 Script 的最新 Timeline，从已有 video clips 同步重建分镜支撑帧。
- Timeline spec 无 shot plan 时优先映射 video clips，只有不存在 video track 时才退回 dialogue clips。
- 增加 API 集成测试，覆盖稳定 clip 映射及不触发 provider pipeline 的复用路径。
- 同步更新 Production Canvas 设计说明和任务板状态。

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/audio/test_storyboard_from_timeline_spec.py tests/integration/test_production_canvas_api.py tests/integration/test_production_canvas_timeline_reuse.py tests/integration/test_production_canvas_media_api.py -q` -> 14 passed.
- `python scripts/check_repo_contracts.py --mode diff <changed-files>` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `pre-commit run --files <changed-files>` -> passed, including backend quick gate.
- `./docker/build_prod_images.sh` -> passed for backend and frontend multi-arch images.

## Next Steps

- 在 `dev_in_docker` 中复验 Timeline reuse 后的视频候选执行。
- 继续完成 provider-backed 视频选用与 stable Timeline clip 回填的集中回归。

## Linked Commits

- Pending
