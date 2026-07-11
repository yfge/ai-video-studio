## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 为图定义编辑提供可发现、可快捷操作的撤销和重做。
- 撤销布局或配置时不回滚候选评审、任务状态和执行证据。

## Changes

- 新增上限为 50 步的图定义历史 reducer，支持连续节点拖拽合并为一步。
- 定义快照覆盖生产节点、配置输出、类型化边和场景/剧集分区；视口、运行证据和评审字段保持当前状态。
- 工具栏增加撤销/重做按钮，画布支持 Cmd/Ctrl+Z、Cmd/Ctrl+Shift+Z 和 Ctrl+Y。
- 将图编辑更新与任务同步、候选审批、Run 恢复更新分流；恢复或重置画布时清空历史。

## Validation

1. Local checks:

- 前端完整测试：310 passed；其中 definition、Board、Keyboard、Selection 定向测试 33 passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- `cd ai-pic-frontend && npm run build`：Next.js production build 通过。
- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过；Board 与 RunPersistence 均为 249 行。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend 生产镜像构建通过，未 push。

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas`
- User path: 空 Run 画布添加便签；分别用工具栏和 Meta+Z / Meta+Shift+Z 撤销、重做；最后重置。
- Console: 仅 React DevTools 与 HMR 信息，0 error/warn。
- Network: 空 Run ID 的本地定义编辑未发送 API 请求，符合保存前本地历史语义。
- Result: 节点数依次为 0 -> 1 -> 0 -> 1 -> 0 -> 1 -> 0；undo/redo enabled 状态每步匹配。
- Evidence: `artifacts/runs/canvas-undo-redo-20260711T220000Z/evidence.json`。

3. Conflict signals and corrections:

- 首次 build 发现 history reducer 联合类型未完全收窄；拆分 action discriminants 后 build 通过。
- 首次 contracts 检查发现 Board 和 RunPersistence 超过 250 行；复用焦点命令并去除空行后均降至 249 行。

## Next Steps

- 实现 Run Ready、Resume、Cancel 和 original/current definition retry。

## Linked Commits

- This commit
