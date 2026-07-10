# Canvas Render Resume

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 页面刷新或重新打开 Canvas run 后，自动续接已保存的 active RenderJob。
- 避免同一 Render Skill 的旧 attempt 或本页已有轮询重复请求。
- 用 dev 内置浏览器证明 reload 后无需再次点击即可拿到成片终态。

## Changes

- Canvas execution tracker 接收当前 run id，并在 run 恢复时读取标准化 saved state。
- 从每个 Render Skill 的 active evidence 中选择 render_job_id 最大的 attempt，自动续接 Timeline render-jobs 轮询。
- 切换 run 时清理旧 Render 定时器和 tracking context；本页已存在的新执行优先，恢复请求不会覆盖它。
- Planner 仅将已有 currentRunId 接入 tracker；未改动当前 Canvas interaction WIP。
- 增加无需点击即可从 restored run state 续接 RenderJob 的 hook 回归测试。

## Validation

- Focused Canvas render suites: 9 passed.
- 全部前端测试排除工作区已知 dirty `toastProvider.test.tsx`: 252 passed, 0 failed.
- `npm run lint`: 0 errors，3 个既有 warnings。
- `npx tsc --noEmit`: 本次 tracker 类型错误已清零；命令仍被工作区既有未提交测试类型错误阻断。
- `python scripts/check_repo_docs.py`: passed.
- Scoped `python scripts/check_repo_contracts.py --mode diff ...`: passed.
- 内置浏览器在独立 run `e3b231c1faa04a4ea048db9e86d4aec6` 执行 Render #125；saved state 与 RenderJob 均为 running/35% 后直接 reload。
- Reload 后未再次点击 Render；恢复页自动从 running/35% 更新为 succeeded/100%，生成 output asset #378 并显示“打开成片”。
- Run saved state 中 `skill-timeline-render-render-125` 最终为 ready/succeeded/100，action label 为“打开成片”。
- 浏览器 Console warn/error 为空；截图：`artifacts/runs/canvas-render-resume-20260710T1450Z/render-125-resumed-after-reload.jpg`。
- 验证 Timeline #73 和 Render #125 已软删除；Episode 138 / Script 130 的活跃最新 Timeline 保持为 #71 v6。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`: backend/frontend production images built locally without push；Next.js production build passed.

## Next Steps

- 将 Render execute evidence 同步持久化到 Canvas run，消除 autosave 前立即刷新丢失 active evidence 的窗口。
- 继续将剩余未提交 Canvas interaction WIP 拆成独立提交。

## Linked Commits

- `28ad12c8` - `feat(canvas): poll render job evidence`
- This commit (pending)
