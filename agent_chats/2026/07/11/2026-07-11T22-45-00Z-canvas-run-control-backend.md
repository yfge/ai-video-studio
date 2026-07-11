## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 在服务端补齐 Run Ready、Resume、Cancel 和 original/current definition retry 语义。
- 复用类型图求值、现有任务状态机和节点执行器，不让浏览器自行判断依赖就绪。

## Changes

- 新增 Run action API：`POST /api/v1/production-canvas/runs/{run_id}/actions`。
- Run Ready 按服务端拓扑顺序执行当前 ready 节点；Resume 跳过已有有效指纹的节点，仅继续失败、取消、stale 或未完成节点。
- Cancel 调用现有 `TaskControlService` 取消 Run 绑定的 pending/processing 任务，并保留节点已完成输出。
- 每次节点执行追加不可变 attempt 摘要，同时内部保存当时节点定义和入边快照。
- Retry 可显式选择失败 attempt 的 original definition 或当前保存 definition。

## Validation

- `pytest tests/integration/test_production_canvas_run_control_api.py -q`：4 passed。
- production canvas 全部单元/集成测试及 task cancel 测试：58 passed。
- 后端完整 `pytest`：2454 passed，88 skipped，0 failed。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- backend/frontend 生产镜像构建通过，`BUILD_PUSH=false`，未 push。

## Next Steps

- 前端接入 Run Ready、Resume、Cancel 与 retry definition 选择，并做真实浏览器 API 验证。

## Linked Commits

- This commit
