## User Prompt

继续完善无限画布功能。整体链路还是断的，可以拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- 让画布 Timeline 执行以当前 Timeline clips 重建 storyboard 支撑帧，而不是复用过期 storyboard。
- 将画布环境/IP 图片引用传播到 Timeline 自动分镜图片子任务。
- 为自动分镜图片任务选择可用的默认图片模型，并以 dev 真实任务验证链路。

## Changes

- Timeline skill 固定传入 `overwrite_storyboard=true`，保证 storyboard 支撑视图跟随当前 Timeline clips。
- 解析画布 `reference_artifacts`，将图片 URL 传入 Timeline pipeline，并在 skill outputs 中记录引用解析证据。
- Timeline pipeline 将全局参考图继续传给自动分镜图片队列；存在全局参考图时，所有 Timeline clip 帧均可入队。
- 自动分镜图片子任务未指定模型时默认使用 `gpt-image-2`，并将自动支撑图收敛为每个 clip 单张起始帧，避免 20 clips × 首尾帧 × 4 候选触发任务超时；显式图片候选流程不受影响。
- 补充 Timeline skill、引用解析、Timeline import 和图片队列回归测试。

## Validation

- `python -m pytest tests/integration/test_production_canvas_api.py::test_production_canvas_execute_timeline_skill_dispatches_existing_task tests/integration/test_production_canvas_reference_artifacts_api.py tests/integration/test_timeline_pipeline_import_api.py tests/unit/services/script/test_timeline_storyboard_queue.py tests/unit/test_storyboard_image_task_reference_requirement.py -q`: 10 passed.
- `python run_tests.py quick --no-setup`: 2407 passed, 77 skipped, 20 deselected.
- `pytest -q`: 2417 passed, 88 skipped.
- Scoped `pre-commit run --files ...`: passed, including backend quick gate and repository contracts.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff ...`: passed; `storyboard_image_autogen.py` remains at the 250-line hard limit.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`: backend and frontend production images built locally.
- Dev task `#6277`: rebuilt 20 Timeline clip frames but reproduced all frames skipped with `reason=no_reference_images`.
- Dev task `#6278`: completed as `timeline:71:v5`; resolved `environment_images:13:1`, reported `reference_image_count=1`, rebuilt 20 Timeline clip frames, and queued all 20 into child task `#6279` with zero skipped.
- Dev task `#6279`: failed with `SoftTimeLimitExceeded()` after processing 20 clips as start/end × 4 candidates; because the processor commits frames at the end, coverage remained 0/20. This reproduced the automatic workload defect fixed by the single-support-frame payload.
- Dev task `#6280`: completed as `timeline:71:v6` after deploying the bounded automatic support-frame payload; child task `#6281` used `model=gpt-image-2`, `keyframe_mode=single`, `count=1`, 20 clip indexes, and one environment reference image.
- Dev task `#6281`: completed in 21m15s with 20/20 provider calls successful and zero generation failures. Database verification found 20 Timeline clip frames, 20 with `start_image_urls`/`image_url`, and zero end images as intended for automatic support frames.
- In-app browser: canvas run `48d62cd56e1646c4b3f0c77c1a3cd4a6` showed task `#6280` completed with `timeline:71:v6` and `reference_image_count=1`; task page `#6281` showed completed with `gpt-image-2`, single-frame mode, count 1, all 20 indexes, and the environment reference. Neither page emitted warning/error console messages. Evidence: `artifacts/runs/canvas-timeline-clip-images-20260710T1242Z/timeline-parent-6280-v6.png` and `artifacts/runs/canvas-timeline-clip-images-20260710T1242Z/storyboard-images-6281-completed.png`.

## Next Steps

- Surface auto-created image child tasks in canvas evidence without requiring manual task IDs.
- Re-run video candidates after clip image coverage is available, then verify render/export coverage.
- Align the visible production chain copy and planner order with `audio -> timeline -> clip -> render -> export`.

## Linked Commits

- Pending.
