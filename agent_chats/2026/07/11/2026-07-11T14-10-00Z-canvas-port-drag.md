## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 让类型化端口支持直接拖拽连线。
- 在空白画布释放时发现可兼容的现有生产节点。

## Changes

- 输入/输出端口升级为可访问交互控件。
- 拖拽输出端口时展示连接预览，释放到兼容输入端口后创建类型化边。
- 释放到空白画布后展示兼容节点弹层，选择后创建相同类型化边并定位目标。
- 复用现有兼容端口算法和 `handleAddEdge` 图状态路径。

## Validation

- 前端端口拖拽、typed-port 与 Board 定向测试：13 passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- 内置浏览器恢复 Run `d2205708bad847a39edbabf84c0bce60`：直接拖拽创建 `Brief Skill -> Asset Selection` 类型化边；空白释放显示 3 个兼容候选，选用后创建边并定位目标；清理测试边后恢复 8 条原有边，console error/warn 为 0。
- 浏览器证据：`artifacts/runs/canvas-port-drag-20260711T141000Z/`。
- `cd ai-pic-frontend && npm run test`：303 passed。
- `cd ai-pic-frontend && npm run build`：Next.js production build 通过。
- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- `pre-commit run --files <本提交文件>`：全部通过。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：后端与前端生产镜像构建成功，未推送。

## Next Steps

- 实现场景/集分区、多选、对齐和生产节点复制。

## Linked Commits

- This commit
