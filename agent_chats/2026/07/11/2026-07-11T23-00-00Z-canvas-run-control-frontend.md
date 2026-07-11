## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 在画布中接通服务端 Run Ready、Resume、Cancel。
- 让失败节点显式选择 original 或 current definition 后重试。

## Changes

- Run 控制区新增运行就绪节点、继续运行和取消运行命令。
- 执行型 Run action 先保存当前图定义，再调用服务端 action；Cancel 直接停止活动任务。
- action 成功后以服务端返回的完整 Run 替换本地状态，不由前端推断 readiness。
- 失败节点恢复区新增重试定义下拉框，支持当前保存定义和失败时原始定义。
- 增加 Run action API types、client endpoint、状态 hook 与自动化测试。

## Validation

1. Local checks:

- 前端完整测试：311 passed。
- Run action、Run controls、retry 与 Board 定向测试：22 passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- `cd ai-pic-frontend && npm run build`：Next.js production build 通过。
- `python scripts/check_repo_docs.py` 与 diff contracts：通过。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：前后端生产镜像构建通过。

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas`
- Run ID: `cc9bf0ffb81a4762af6fa7b9094fded0`
- User path: 创建隔离 Run，依次点击运行就绪节点、继续运行、取消运行。
- UI result: `已运行就绪节点 · 2 个节点`、`已继续未完成节点 · 1 个节点`、`已取消活动任务`；三个控制均保持可用。
- Network: Run Ready `req-1783780118666-iiqycx1n`、Resume `req-1783780159735-ayvkpkix`、Cancel `req-1783780160517-e47tyeg3` 均为 `POST /api/v1/production-canvas/runs/{run_id}/actions` 200。
- Console: 0 error/warn。
- Evidence: `artifacts/runs/canvas-run-controls-20260711T223000Z/`。

3. Conflict signals and corrections:

- 首次创建请求因浏览器会话过期返回 401；重新使用仓库测试账号登录后，以同一路径创建新 Run 并完成三项 action 验证。

## Next Steps

- 逐项审计设计文档验收条件并更新当前状态说明。

## Linked Commits

- Backend Run controls: `efcfec5f`
- This commit
