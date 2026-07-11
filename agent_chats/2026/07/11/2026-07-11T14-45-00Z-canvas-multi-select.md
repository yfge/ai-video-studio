## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 支持多个节点的批量空间编辑。
- 复制生产节点时保留配置但隔离旧执行证据。

## Changes

- Shift/Cmd/Ctrl 支持节点多选，组拖拽和方向键同时移动选中节点。
- 增加左对齐、顶对齐、水平分布和垂直分布。
- 复制选中生产节点及选中子图内部边，清理任务、产物和审批证据。
- 多选保持为会话态，不进入服务器画布定义。

## Validation

- 前端 selection、Board、keyboard 与 notes 定向测试：38 passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- `cd ai-pic-frontend && npm run build`：Next.js production build 通过。
- 内置浏览器临时无 Run 画布：Shift 选中 `brief + script`，左对齐后 X 均为 40；复制生成两个选中副本及其内部类型化边；重置后副本为 0，console error/warn 为 0。
- 浏览器证据：`artifacts/runs/canvas-multi-select-20260711T144500Z/`。
- `cd ai-pic-frontend && npm run test`：306 passed。
- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- `pre-commit run --files <本提交文件>`：全部通过。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：后端与前端生产镜像构建成功，未推送。

## Next Steps

- 增加场景/集分区及持久化 schema。

## Linked Commits

- This commit
