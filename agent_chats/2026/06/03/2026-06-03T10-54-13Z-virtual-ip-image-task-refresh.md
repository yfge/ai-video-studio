## User Prompt

用户报告已完成的“虚拟IP文生图 - 老拐”任务没有在前台 IP 页面看到。

## Goals

- 追踪任务、图片落库、图片列表 API 和前端渲染链路。
- 修复异步图像生成完成后前台 IP 图片列表不刷新的问题。
- 保留已有未提交改动，不触碰无关文件。

## Changes

- 确认任务 `5991` 已完成并写入 `result_file_path=virtual_ip_image:1:144`。
- 确认 `/api/v1/virtual-ips/1/images` 已返回图片 `144`，问题在前端状态刷新链路。
- 为虚拟 IP 图片页新增异步任务轮询刷新：创建文生图/图生图任务后跟踪 task id，任务完成后静默刷新图片列表。
- 为图片数据 hook 增加窗口重新获得焦点和可见性恢复时的静默刷新。
- 补充前端测试覆盖异步任务刷新链路。

## Validation

- `cd ai-pic-frontend && npm run lint` 通过；保留仓库既有 18 个 warning。
- `cd ai-pic-frontend && npm run test` 通过；31 tests pass。
- `cd ai-pic-frontend && npm run build` 通过。
- `python scripts/check_repo_docs.py` 通过。
- `python scripts/check_repo_contracts.py --mode diff ...` 通过。
- In-app Browser 验证 `/virtual-ip/233525e9045146d580a1d18ef4a28161#ip-images` 可见 `image_id=144` 对应的 `03/06/2026` 肖像卡片。
- 浏览器证据：`artifacts/runs/virtual-ip-image-task-refresh-20260603T105413Z/old-gui-image-144-visible.png` 与 `browser-evidence.json`。

## Next Steps

- 无。

## Linked Commits

- This commit.
