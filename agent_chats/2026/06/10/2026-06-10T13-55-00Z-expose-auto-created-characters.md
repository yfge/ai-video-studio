---
id: 2026-06-10T13-55-00Z-expose-auto-created-characters
date: "2026-06-10T13:55:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - backend
  - frontend
  - episode-characters
related_paths:
  - ai-pic-backend/app/services/script/generation_task_attempts.py
  - ai-pic-frontend/src/components/features/episode/autoCreatedCharactersFromScript.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceActiveTabContent.tsx
  - ai-pic-frontend/tests/autoCreatedCharactersFromScript.test.ts
summary: async 剧本生成自动创建的临时角色持久化到 script.extra_metadata 并在角色 tab 展示绑定提醒——此前前端硬编码空数组，横幅在任何路径都不可见。
---

# Expose Auto-Created Characters After Script Generation

## User Prompt

生产链路优化 Phase B2：剧本生成会自动为陌生角色名创建 Episode 临时角色，但 async 路径下 `parse_ai_content` 只解析 result.content，顶层的 `auto_created_characters` 被丢弃；且前端 `WorkspaceActiveTabContent` 硬编码 `autoCreatedCharacters={[]}`，绑定提醒横幅在 sync/async 任何路径都是死的。

## Goals

- 后端：async 生成把 `auto_created_characters` 持久化到 `script.extra_metadata`。
- 前端：角色 tab 从选中剧本的 extra_metadata 读取并展示自动创建横幅（A3 的完成自动选中使 async 路径闭环）。

## Changes

- `generation_task_attempts.py`：attempt 返回前把顶层 result（agent + quality gate 两条路径都会写入）的 `auto_created_characters` 并入 `ai_content`，经 `build_generation_extra_metadata` 的非排除键透传持久化。
- 新增前端 helper `autoCreatedCharactersFromScript`（类型守卫过滤畸形条目）。
- `WorkspaceActiveTabContent`：`autoCreatedCharacters={autoCreatedCharactersFromScript(selectedScript)}` 替换硬编码 `[]`。
- 新测试 `tests/autoCreatedCharactersFromScript.test.ts`（有效条目读取 / 畸形与缺失容错）。

## Validation

- 后端 `pytest -k "generation_task or script_generation"`（排除两组预先存在的收集错误模块，已用 git stash 验证其在 HEAD 即失败）：8 passed。
- 前端 `npm run test`：70 个测试全部通过；`npm run lint` 0 errors。

## Next Steps

- B3：渲染完成 toast + 下载按钮。
- 跟进（独立问题）：`tests/unit/services/ai/test_scripts_ai_manager.py` 与 `tests/scripts/test_production_*_score.py` 收集错误为预先存在的测试漂移（`_BEAT_CONTRACT_MAX_TOKENS` 等符号已不存在），需单独修复。

## Linked Commits

- This commit.
