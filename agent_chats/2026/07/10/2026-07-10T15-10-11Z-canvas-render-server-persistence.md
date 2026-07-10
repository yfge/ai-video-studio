# Canvas Render Server Persistence

## User Prompt

继续完善无限画布功能，保持原子化提交；整体链路仍然是断的，可拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- Render execute 成功后立即把 active execution evidence 写入对应 Canvas run。
- 消除浏览器 autosave 前刷新导致 RenderJob 无法自动续接的窗口。
- 保持浏览器已保存 evidence 的现有恢复路径，并用真实页面证明立即刷新后无需重复点击。

## Changes

- Canvas run persistence 在行锁保护下按 skill 原子 upsert 最新 execution result，并让 saved state 写入使用同一锁。
- Production Canvas execute 在请求携带有效 run id 时立即持久化 skill result；无效或非当前用户 run 保持原有 execute 行为。
- 恢复 tracker 将服务端 active Render 节点覆盖到可能滞后的 saved state，同时保留浏览器保存的布局和 evidence。
- 当服务端已有 queued/running Render result 但浏览器尚未 autosave evidence 时，合成对应 Render evidence 并自动续接轮询。
- 拆分恢复测试，分别覆盖浏览器已保存 evidence 和服务端先持久化 execution 两条路径。

## Validation

- Backend focused tests: 4 passed.
- Full backend suite: 2421 passed, 88 skipped.
- Focused Canvas execution/render suites: 10 passed.
- 全部前端测试排除工作区已知 dirty `toastProvider.test.tsx`: 253 passed, 0 failed.
- `npm run lint`: 0 errors，3 个既有 warnings。
- `python scripts/check_repo_docs.py`: passed.
- Scoped `python scripts/check_repo_contracts.py --mode diff ...`: passed.
- Changed backend files passed `ruff check` and `black --check`.
- 内置浏览器在独立 run `21c2af39cdaa45dd81e8ddf51703cd40` 执行 Render #126，并在点击后 352ms、浏览器 autosave 前直接 reload。
- Reload 时 run `saved_state` 尚无 Render evidence，但服务端 `skill_results` 已保存 timeline.render running 和 render_job_id 126；页面无需再次点击即合成 `Render #126`、恢复轮询并更新为 succeeded/100%。
- Render #126 输出 asset #379，最终 evidence 显示“打开成片”；Console warn/error 为空。截图：`artifacts/runs/canvas-render-immediate-resume-20260710T1505Z/render-126-immediate-refresh.jpg`。
- 验证 Timeline #74 和 Render #126 已软删除；Episode 138 / Script 130 的活跃最新 Timeline 保持为 #71 v6。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`: backend/frontend production images built locally without push；Next.js production build passed。

## Next Steps

- 在原始 Canvas run 上复核既有 Render #122 / Timeline #71 v6 / asset #375 回归。
- 继续把剩余未提交 Canvas interaction WIP 拆成独立提交。

## Linked Commits

- `c9bfab18` - `feat(canvas): resume render polling on restore`
- This commit (pending)
