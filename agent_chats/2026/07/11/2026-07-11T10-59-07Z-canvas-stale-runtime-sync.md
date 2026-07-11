## User Prompt

继续完善无限画布功能，保证整体链路可用并使用 dev_in_docker 与内置浏览器检验。

## Goals

- 让后端保存时判定的 stale 节点无需刷新即可反映到当前画布。
- 在前端保存和恢复链路中保留执行输入指纹。
- 不让较晚返回的保存响应覆盖用户正在进行的画布布局修改。

## Changes

- 为前端画布节点和保存 API 类型增加执行输入指纹字段，并完成序列化与恢复映射。
- 保存成功后仅把服务端拥有的节点状态和执行指纹合并到当前画布，保留本地布局、连线、视口和选择状态。
- 增加保存响应触发 stale 即时显示的钩子测试，并验证请求继续携带原执行指纹。

## Validation

- `cd ai-pic-frontend && npm run lint`：通过，保留 3 个既有 warning，无 error。
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvas*.test.ts tests/productionCanvas*.test.tsx`：159 passed。
- `cd ai-pic-frontend && npm run build`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：前后端生产镜像本地构建通过，未推送。
- dev_in_docker / 内置浏览器：Run `d2205708bad847a39edbabf84c0bce60` 先运行 Brief Skill 下游建立指纹，再移除 Brief Skill 到 Asset Selection 的类型化连线；自动保存后 Asset Selection 无需刷新即显示“已过期”。
- 数据库：Task `6289` 中 `skill-asset-select` 状态为 `stale`，执行指纹存在，保存边数为 7。
- 浏览器 console error/warn：空。
- 截图：`artifacts/runs/canvas-stale-20260711T110000Z/stale-after-save.jpg`。

## Next Steps

- 实现媒体候选的画布内审阅、选定输出和重跑操作。
- 将选定候选作为类型化输入贯通到 Timeline 节点。

## Linked Commits

- This commit
