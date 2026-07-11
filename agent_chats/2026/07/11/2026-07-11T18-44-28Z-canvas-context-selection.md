## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 满足操作员不复制 Episode 或 Script ID 即可建立画布生产上下文的退出标准。
- 用真实 API 验证剧集列表与按剧集过滤的剧本列表。
- 将改动作为独立、可审查的前端切片提交。

## Changes

- 将剧集和剧本数字输入改为按名称显示的级联选择器。
- 从现有 Episode API 加载当前用户可访问的剧集；选择剧集后只加载该剧集的剧本。
- 切换剧集时清除旧剧本选择，避免向新剧集发送不兼容的 `script_id`。
- 更新 Planner 测试夹具，使测试也通过真实下拉交互建立上下文。
- 在画布设计现状与验收标准中记录无需复制业务 ID 的上下文选择路径。

## Validation

1. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/productionCanvasPlanner.test.tsx tests/productionCanvasChatBar.test.tsx` -> 14 passed。
- `cd ai-pic-frontend && npm run lint` -> 0 errors，3 个既有 warnings。
- `cd ai-pic-frontend && npm run test` -> 325 passed。
- `cd ai-pic-frontend && npm run build` -> 通过，`/canvas` production route 成功生成。
- `python scripts/check_repo_docs.py` -> 通过。
- `python scripts/check_repo_contracts.py --mode diff ...` -> 通过。

2. Browser validation:

- Entry URL: `http://localhost:8089/canvas`。
- User path: 重置为干净画布，按名称选择 IP 84、环境 13、剧集 49、剧本 30。
- Console: 内置浏览器 warning/error 日志为空。
- Network/runtime: 后端日志确认 `GET /api/v1/episodes?limit=100` 200，随后 `GET /api/v1/scripts?episode_id=49&limit=100` 200。
- Result: 页面选中值为 `virtual_ip_id=84`、`environment_id=13`、`episode_id=49`、`script_id=30`；截图为 `artifacts/runs/canvas-context-selection-20260712T030000Z/context-selected.png`。

3. Conflict signals and corrections:

- Initial assumption: 现有全量测试可直接覆盖上下文输入改动。
- Contradicting evidence: Planner 测试仍查找已删除的“剧集 ID”输入框，325 项中 1 项失败。
- Correction: 测试夹具增加 Episode/Script 列表响应，测试改为聚焦、加载并选择剧集下拉；重跑后 325/325 通过。

## Next Steps

- 用当前选中的生产上下文创建新 Run，完成 provider-backed 图片候选到 Timeline 回填的统一浏览器回归。

## Linked Commits

- Pending
