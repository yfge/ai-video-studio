## User Prompt

继续完善无限画布功能；更新设计文档；先提交现有变更；继续。

## Goals

- 定义可回归的大规模画布结构性能预算。
- 在不削弱筛选、小地图和连线发现完整性的前提下减少重节点 DOM。
- 用单元测试和真实内置浏览器记录规模证据。

## Changes

- 为超过 80 个逻辑可见节点的画布增加视口加 240px overscan 的节点卡片虚拟化。
- 强制保留选中和执行中的离屏节点，并只绘制两个端点均已挂载的边。
- 保持小地图、筛选、分区和连线发现使用完整逻辑图。
- 定义 500 节点、1,000 边、100 分区的基线和 60 个重节点卡片挂载预算。
- 将 Phase 4 的规模化任务和设计状态更新为完成。

## Validation

- `cd ai-pic-frontend && npx tsx --test tests/productionCanvasVirtualization.test.ts`：3 passed。
- `cd ai-pic-frontend && npx eslint src/components/features/canvas/ProductionCanvasSurface.tsx src/components/features/canvas/productionCanvasVirtualization.ts tests/productionCanvasVirtualization.test.ts`：通过。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- `cd ai-pic-frontend && npm run test`：325 passed。
- `cd ai-pic-frontend && npm run build`：通过，`/canvas` production route 成功生成。
- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- 内置浏览器 `http://localhost:8089/canvas`：插入子流程后显示 107/107 个逻辑节点，`data-rendered-node-count=3`，小地图有 107 个节点定位入口；截图为 `artifacts/runs/canvas-scale-20260712T023000Z/scale-107-nodes.png`。

## Next Steps

- 发布前在当前环境完成一次统一 provider-backed 图片候选到 Timeline 回填整链复验。

## Linked Commits

- Pending
