## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 支持在大型制作图中搜索并按生产上下文筛选节点。
- 保持筛选与持久化图定义相互独立。

## Changes

- 增加节点搜索以及场景、节点类型、状态和负责人筛选。
- stale 节点通过状态 facet 直接筛选。
- 筛选只隐藏不匹配节点及其悬空边，不修改节点、边、坐标或 autosave 状态。
- 增加匹配计数、定位首项、清除筛选和无结果状态。

## Validation

- 前端定向测试：9 passed。
- `cd ai-pic-frontend && npm run test`：298 passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- 内置浏览器恢复 Run `d2205708bad847a39edbabf84c0bce60`：原图 22 节点/8 条边；stale 筛选仅显示 `skill-asset-select`，搜索“镜头顺序”仅显示并定位 `timeline`，筛选边均无悬空端点，console error/warn 为 0。
- 浏览器证据：`artifacts/runs/canvas-node-filters-20260711T130500Z/`。
- `cd ai-pic-frontend && npm run build`：Next.js production build 通过。
- `pre-commit run --files <本提交文件>`：全部通过。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：后端与前端生产镜像构建成功，未推送。

## Next Steps

- 实现小地图与选中节点导航。

## Linked Commits

- This commit
