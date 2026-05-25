## User Prompt

按项目规范，依次完成对应计划，保证原子性提交

## Goals

- Package the current worktree according to repository commit discipline.
- Keep commits atomic across Timeline render/export, Codex/ChatGPT provider, Virtual IP DeepSeek content fill, and readiness docs.
- Attempt the next `Episode -> Timeline -> Render -> Export` readiness phase with real local services.
- Update active planning docs with the real Phase 1 and Phase 2 state.

## Changes

- Created four atomic commits for the existing worktree boundaries:
  - `95857e9b feat(timeline): close render export loop`
  - `8251d67f feat(ai): add codex chatgpt provider`
  - `657b3a35 fix(virtual-ip): use deepseek flash for content fill`
  - `7bade488 docs(timeline): add main chain readiness plan`
- Updated `tasks.md` and `docs/exec-plans/active/main-chain-commercial-readiness.md` to mark Phase 1 closure complete.
- Recorded the Phase 2 harness attempt and the current blocker: Timeline video clips do not resolve to legacy storyboard/video task video assets.

## Validation

- `git diff --check`: passed after the four atomic commits.
- `python scripts/check_repo_docs.py`: passed after the four atomic commits.
- `python scripts/check_repo_contracts.py --mode audit`: passed after the four atomic commits.
- `curl -fsS --max-time 5 http://localhost:8000/health`: backend healthy.
- `curl -fsS --max-time 5 http://localhost:8089/`: frontend/nginx reachable.
- `docker exec ai-video-backend python -c "from app.services.render import TimelineRenderService; print(TimelineRenderService.__name__)"`: passed, confirming the running backend imports the Timeline render service.
- `python scripts/harness/run_golden_path.py --scenario timeline_export_end_to_end --run-id main-chain-e2e-20260525T031832Z --api-url http://localhost:8000 --base-url http://localhost:8089 --username geyunfei --password '<redacted>' --script-id 122 --timeout-seconds 300`: failed as expected for the current data state. The request chain reached login, `/auth/me`, timeline pipeline queueing, task polling, script read, timeline list, render queueing, and render-job polling. Render job `1` failed with `missing_video_url` for 30 clips and no `output_asset`; task `5986` failed with `storyboard_has_assets_refuse_overwrite: set overwrite_existing=true`.
- Database checks showed `video_generation_tasks` has succeeded rows for script `122`, but storyboard frames do not have `timeline_clip_id` and `media_assets` is empty, so current assets cannot satisfy Timeline clip resolution.

## Next Steps

- Implement or backfill clip asset lineage so storyboard/video task assets can attach to stable Timeline `clip_id`.
- Then rerun `timeline_export_end_to_end` until a render job reaches `succeeded` with `output_asset.file_url` or `output_asset.file_path`.
- Continue with Timeline delete/rollback only after the real render/export evidence gap is closed.

## Linked Commits

- Pending.
