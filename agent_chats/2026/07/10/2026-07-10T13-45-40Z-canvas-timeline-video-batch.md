# Canvas Timeline Video Batch

## User Prompt

继续完善无限画布功能；现在整体链路还是断的。可以拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- 让生产画布的 Video Candidates 生成结果绑定到当前 Timeline 版本和具体 video clip。
- 让批量视频任务完成后保留可追踪的 Timeline 结果引用。
- 在 dev 环境验证画布视频候选、Timeline 资产解析和最终 render/export 链路。

## Changes

- Video Candidates 现在只接受来自当前 Timeline 版本的 storyboard 支撑帧，并为每帧下发 `timeline_rework` clip 上下文。
- 每个子视频任务保留 Timeline id/version、clip id、`generated_video` 资产角色和 provider lineage；批次不自动触发逐 clip render。
- 画布批次使用各 Timeline clip 的镜头提示词，不再用画布整体目标覆盖全部视频提示词。
- 批次完成结果改为 `timeline_videos:<timeline_id>:v<version>:<count>`，画布输出同时记录 Timeline 映射数量。
- 增加画布 API 集成测试、子任务 Timeline 上下文测试和父任务结果引用测试。

## Validation

- `cd ai-pic-backend && python -m pytest tests/integration/test_production_canvas_media_api.py tests/unit/services/video/test_storyboard_video_timeline_submission.py tests/unit/services/video/test_video_task_polling_parent_task.py -q`: 8 passed.
- `cd ai-pic-backend && python run_tests.py quick --no-setup`: 2409 passed, 77 skipped, 20 deselected.
- `cd ai-pic-backend && python -m pytest -q`: 2419 passed, 88 skipped.
- Scoped `pre-commit run --files ...`: passed Ruff, Black, isort, docs drift, repository contracts, ledger enforcement, and backend quick gate.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff ...`: passed.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`: backend and frontend production images built locally without push.
- Dev canvas run `48d62cd56e1646c4b3f0c77c1a3cd4a6`: task #6282 completed one clip, task #6283 completed the remaining 19 clips with result `timeline_videos:71:v6:19`.
- Timeline 71 v6 resolved 20/20 video clips from `timeline_clip_asset:provider_rework`; no missing or generating clips remained.
- In-app browser at `/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6` showed task #6283 completed with Timeline 71 v6 and 19 mapped clips; Console had no warnings or errors.
- In-app browser at `/episodes/138/workspace?tab=timeline&scriptId=130` showed 20 renderable clips and render #122 completed with output asset #375.
- Render #122 succeeded with 20 clips, original episode audio, 9 subtitles, and a 120000 ms output asset. `ffprobe` confirmed H.264 video plus AAC audio at 121.416667 seconds.
- Browser screenshots and media probe are stored under `artifacts/runs/canvas-timeline-videos-20260710T1330Z/`.

## Next Steps

- Add explicit Render/Export nodes and task evidence to the production canvas instead of requiring the Episode Timeline workspace for the final action.
- Reorder the visible canvas production header so it reflects the Timeline-first media contract.

## Linked Commits

- `6e592b5d` - `fix(canvas): seed timeline clip support frames`
- This commit (pending)
