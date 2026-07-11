## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 将原始后端与供应商数据移出画布节点的主要业务视图。
- 通过显式入口保留问题诊断能力。

## Changes

- 新增高级诊断 disclosure，默认折叠后台复用目标和原始执行输出。
- Inspector 继续直接展示节点状态、业务说明和执行操作。
- 任务板新增 Production Canvas Phase 3 的可执行清单。

## Validation

- `cd ai-pic-frontend && npm run test -- --test-name-pattern='ProductionCanvasPlanner|ProductionCanvasBusyActions'`：295 passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- 内置浏览器恢复 Run `d2205708bad847a39edbabf84c0bce60`：高级诊断默认折叠，点击后后台复用与执行输出可见，console error/warn 为 0。
- 浏览器证据：`artifacts/runs/canvas-advanced-diagnostics-20260711T124600Z/`。
- `pre-commit run --files <本提交文件>`：全部通过；全仓运行命中历史文件既有格式和 ruff 债务，自动改动已撤销。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：后端与前端生产镜像构建成功，未推送。

## Next Steps

- 实现节点搜索与状态筛选。

## Linked Commits

- This commit
