## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 在画布内展示真实持久化图片候选和生成元数据。
- 让操作员显式选用候选，并立即采用服务端 Run 审核状态。
- 确保选用状态、资产身份和类型化下游绑定可保存恢复。

## Changes

- 前端 API 增加候选查询与选用请求，并补齐保存节点的 selected output 审核字段。
- 新增候选评审面板，支持图片预览、视频播放、帧/clip/模型/时长信息、原始资产入口、刷新和显式选用。
- 选用成功后从服务端 Run 重建画布状态，显示 approved 状态并保留下游 stale 计算结果。
- 首张可见候选 eager 加载，其余候选懒加载，消除 Next.js LCP 控制台警告。
- 将复制链接测试改为等待 React 可见状态，避免在异步剪贴板完成与状态提交之间竞态。
- 更新 `tasks.md`，将图片候选持久资产、生成历史和人工选用标为完成。

## Validation

- `cd ai-pic-frontend && npm run lint`：通过，保留 3 个既有 warning，无 error。
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvas*.test.ts tests/productionCanvas*.test.tsx`：160 passed。
- `cd ai-pic-frontend && npm run build`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：前后端生产镜像本地构建通过，未推送。
- dev_in_docker / 内置浏览器：Run `d2205708bad847a39edbabf84c0bce60` 使用 script `130` 的既有 frame `0` 图片，画布预览真实资产并选用；节点变为“已选用”，Run 恢复后仍显示相同候选和审核状态。
- 数据库：`media_assets.id=380`，节点 `skill-image-candidates` 为 `approved`、definition version `2`，审核人/时间和 selected-output 边均持久化。
- 新标签页 browser console error/warn：空。
- 截图：`artifacts/runs/canvas-candidate-review-20260711T112440Z/approved-image-candidate-clean.jpg`。

## Next Steps

- 用 approved image 驱动视频候选节点，验证可播放历史、失败重试和人工选片。
- 将 approved video 通过 stable `clip_id` 和 Timeline version 显式回填。

## Linked Commits

- This commit
