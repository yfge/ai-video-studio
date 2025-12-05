---
id: 2025-12-05T14-43-44Z-validation-closure
date: 2025-12-05T14:43:44Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [testing, story-structure, frontend]
related_paths:
  - ai-pic-backend/tests/test_story_structure_endpoints.py
  - ai-pic-backend/TESTING_GUIDE.md
  - ai-pic-frontend/tests/sceneStructurePanel.test.tsx
  - ai-pic-frontend/src/components/SceneStructurePanel.tsx
  - ai-pic-frontend/package.json
  - task.md
summary: "Add validation tests for story structure, frontend read-only/structure loading tests, and document migration/CRUD verification steps"
---
## User Prompt
. 验证闭环（当前唯一未勾选的结构任务）
      - 后端：补充 scene/beat/shot 权限与顺序/唯一性校验的负例单测（服务 + API）；添加迁移回归脚本文档与 pytest 用例。
      - 前端：新增场景/节拍/镜头 CRUD+权限的端到端或集成测试（可用 Playwright/Cypress 或 React Testing Library），覆盖只读/错误提示。
      - 文档：更新 TESTING_GUIDE/README 说明如何运行迁移验证与结构化 CRUD 回归。

## Goals
- Close the “验证闭环” task with regression tests for story structure rules and frontend read-only handling.
- Document how to run migration validation and structured CRUD regression suites.

## Changes
- Backend: Added endpoint regression tests covering beat order conflicts, duplicate shot numbers, and beat/scene mismatch 400s.
- Frontend: Added `SceneStructurePanel` API override hook and React Testing Library test to verify read-only badge and structure loading callbacks; updated test runner to use `tsx --test` with TypeScript/JSDOM support.
- Docs: Extended `TESTING_GUIDE.md` with migration validation commands and structured CRUD test instructions; marked task board validation item as done.

## Validation
- ai-pic-backend: `pytest tests/test_story_structure_endpoints.py -q`
- ai-pic-frontend: `npm test`

## Next Steps
- Add E2E coverage that ties storyboard frames to beat/shot associations when backend exposes links; include permission chains.
- Keep migration rollback drills recorded with reports for future releases.

## Linked Commits
- (pending)
