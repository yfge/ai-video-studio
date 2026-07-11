## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 为大型制作图提供持续可见的空间导航。
- 复用现有选中节点居中能力，不创建第二套 viewport 状态。

## Changes

- 增加画布小地图、节点缩略图、选中状态和当前视口框。
- 点击小地图空白位置平移到对应世界坐标。
- 点击小地图节点复用选中节点居中逻辑。
- 小地图遵循当前搜索和筛选结果。

## Validation

- 前端小地图与 Board 定向测试：10 passed。
- `cd ai-pic-frontend && npm run test`：301 passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- `ProductionCanvasBoard.tsx`：249 行，低于 250 行硬限制。
- 内置浏览器恢复 Run `d2205708bad847a39edbabf84c0bce60`：点击 `Brief Skill` 缩略节点后选中并居中；点击空白位置后 viewport 再次变化且选中节点保持，console error/warn 为 0。
- 浏览器证据：`artifacts/runs/canvas-minimap-20260711T133800Z/`。
- `cd ai-pic-frontend && npm run build`：Next.js production build 通过。
- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- `pre-commit run --files <本提交文件>`：全部通过。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：后端与前端生产镜像构建成功，未推送。

## Next Steps

- 实现端口拖拽连接与空白画布兼容节点发现。

## Linked Commits

- This commit
