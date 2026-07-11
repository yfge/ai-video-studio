## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 完成 approved image 到真实视频任务、候选评审和 Timeline 落位的浏览器链路。
- 展示视频任务进度、失败原因和显式重试操作。
- 修复 Timeline 版本推进、provider 参数、候选物化和画布持久化竞态。

## Changes

- 视频任务状态区展示真实媒体任务 ID、状态、进度/错误，并在失败时复用节点执行链路重试。
- stable clip 在当前 Timeline 仍存在时允许消费较早版本的 storyboard 支撑帧，并记录 source Timeline version。
- MiniMax Hailuo 2.3/02 将通用 720p 请求归一化为支持的 768P。
- Timeline provider rework 资产进入视频候选历史，可直接预览、选用并落位。
- 新任务提交时清理旧任务错误；任务证据恢复只合并 task 字段，不覆盖当前 Timeline 上下文。
- 修复 autosave 确认签名和 server state adoption，停止重复 PUT 与审批状态回滚。
- 媒体候选节点保留自己的 script/Timeline 绑定，避免共享上下文覆盖。

## Validation

- 后端定向测试：候选评审、视频队列版本映射和 MiniMax 分辨率共 6 passed；媒体 API 与版本/分辨率组合共 7 passed。
- `cd ai-pic-backend && pytest -q`：2449 passed，88 skipped。
- `cd ai-pic-frontend && npm run test`：295 passed。
- `npm run lint`：0 errors，3 个既有 warnings。
- `npm run build`：Next.js production build 通过。
- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- dev_in_docker / 内置浏览器：Run `d2205708bad847a39edbabf84c0bce60` 使用 approved image asset 380 创建真实任务 6292；MiniMax provider task `418683134718226` succeeded，生成 asset 382。
- 浏览器显示任务完成、可播放视频（readyState 4，768x768，1.875s）、人工选用和“已放入 Timeline v8”；刷新后状态保持。
- Timeline 71 v8 的 stable clip `video_scene_568_beat_3442_001` 绑定 asset 382，lineage 1446 为 `generated_video`。
- 最终浏览器 console error/warn：空；修复后两分钟窗口内自动保存 PUT：0。
- 证据：`artifacts/runs/canvas-full-chain-20260711T120500Z/`。
- `pre-commit run --files <本提交文件>`：全部通过，包含 backend quick gate 与 frontend lint。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：后端与前端生产镜像构建成功，未推送。

## Next Steps

- 运行完整提交前门槛并原子提交本切片。
- 继续按更新后的设计审计无限画布剩余非主链能力。

## Linked Commits

- This commit
