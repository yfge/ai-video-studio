# Canvas RenderJob Polling

## User Prompt

继续完善无限画布功能；整体链路还是断的，可以拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- 让 Canvas 新建 RenderJob 后自动跟踪 queued、running 和终态。
- 成功后自动回写成片资产链接，失败或取消时给出可重试状态。
- 避免新 RenderJob 执行期间继续暴露上一次成片链接。

## Changes

- 在 Canvas execution tracker 中新增 Timeline RenderJob 轮询，复用现有轮询间隔和超时配置，并在卸载或同节点重跑时停止旧轮询。
- 将 RenderJob 的状态、进度、日志、output asset 和更新时间统一映射到 Render Skill 与 `Render #<id>` 证据节点。
- RenderJob 成功时自动将两个节点更新为可复用并挂载“打开成片”；失败、取消或缺少输出资产时更新为待补齐。
- 新 RenderJob queued/running 时清除上一轮成片链接，避免打开过期产物。
- 增加 helper、hook 和 stale-link 回归测试。

## Validation

- `npx tsx --test tests/productionCanvasExecutionTracking.test.ts tests/productionCanvasExecutionTracker.test.tsx tests/productionCanvasRenderNodes.test.ts`: 8 passed.
- 全部前端测试排除工作区已知 dirty `toastProvider.test.tsx`: 251 passed, 0 failed.
- `npm run lint`: 0 errors，3 个既有 warnings。
- `npx tsc --noEmit`: 本次文件无新增错误；命令仍被工作区既有未提交测试类型错误阻断。
- `python scripts/check_repo_docs.py`: passed.
- scoped `python scripts/check_repo_contracts.py --mode diff ...`: passed.
- 内置浏览器在独立 run `6e3ebcb8fea245938f295e50a95bfa09` 单次执行 Render #124：先显示 queued/0，第一次轮询自动显示 running/35%，随后自动显示 succeeded/100%、output asset #377 和“打开成片”。
- Render #124 API 终态为 succeeded/100；run saved state 中对应 evidence 节点为 ready/succeeded/100，action label 为“打开成片”。
- 浏览器 Console warn/error 为空；截图：`artifacts/runs/canvas-render-polling-20260710T1433Z/render-124-auto-complete.jpg`。
- 验证使用的 Timeline #72 和 Render #123/#124 已软删除；Episode 138 / Script 130 的活跃最新 Timeline 已恢复为 #71 v6。
- dev 网关对带 JSON body 的 DELETE 请求返回 422/body missing，验证数据最终通过数据库同语义软删除字段完成清理。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`: backend/frontend production images built locally without push；Next.js production build passed.

## Next Steps

- 在恢复含 active Render evidence 的 Canvas run 时自动续接轮询，覆盖刷新或重新打开页面的场景。
- 将剩余未提交 Canvas interaction 拆分继续按原子提交收敛。

## Linked Commits

- `2c4a84bd` - `feat(canvas): add render export nodes`
- This commit (pending)
