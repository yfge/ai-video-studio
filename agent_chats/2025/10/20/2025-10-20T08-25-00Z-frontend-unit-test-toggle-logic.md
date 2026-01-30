---
id: 2025-10-20T08-25-00Z-frontend-unit-test-toggle-logic
date: 2025-10-20T08:25:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, testing]
related_paths:
  - ai-pic-frontend/src/utils/storyboardToggle.js
  - ai-pic-frontend/tests/storyboardToggle.test.js
  - ai-pic-frontend/package.json
summary: "Add minimal unit test for storyboard normalized toggle logic using Node test runner."
---

## User Prompt

为分镜页的规范化结构开关编写最小前端单元测试，尽量不引入新依赖。

## Goals

- 提取纯函数帮助逻辑以便测试（选择场景数组、初始化选中场景号、映射选中场景号）。
- 使用 Node 20+ 自带 `node:test` 运行最小测试，无需安装依赖。

## Changes

- 新增 `src/utils/storyboardToggle.js`，导出 `selectUiScenes`、`initialSelectedSceneNumber`、`mapNormalizedSceneToSelected`。
- 新增 `tests/storyboardToggle.test.js`，覆盖三类逻辑分支。
- 更新 `package.json` scripts，添加 `test: node --test`。

## Validation

- 测试无需编译与第三方库，适合快速冒烟验证逻辑正确性。

## Next Steps

- 若后续需要更复杂的组件级测试，可引入 Vitest/Jest + React Testing Library（需包管理与网络许可）。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）
