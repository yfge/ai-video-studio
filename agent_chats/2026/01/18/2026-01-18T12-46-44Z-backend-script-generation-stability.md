---
id: 2026-01-18T12-46-44Z-backend-script-generation-stability
date: "2026-01-18T12:46:44Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, script, minimax, fallback]
related_paths:
  - ai-pic-backend/app/services/ai/scripts.py
  - ai-pic-backend/app/services/ai/scripts_ai_manager.py
  - ai-pic-backend/app/services/episode_agent_episode_utils.py
  - ai-pic-backend/tests/unit/services/ai/test_scripts_ai_manager.py
  - ai-pic-backend/tests/unit/services/ai/test_scripts_generation_mixin.py
  - ai-pic-backend/tests/unit/services/test_episode_agent_episode_utils.py
  - tasks.md
summary: "Fix script generation regressions causing mock fallback and single-scene outputs by adding max_tokens/JSON repair, agent timeout controls, and better episode fallback scenes."
---

## User Prompt

- 全局检查文生图/图生图提示词规范，并考虑按 provider 进一步优化与动态输入；原子化分布提交。
- 当前剧集工作台 `http://localhost:8089/episodes/1cca3cc61d7740b4b5f73bccf8fe4d32/workspace` 的剧本内容“扯淡/不及格”，需要定位问题并修复。
- 检查并更新 `tasks.md`。

## Goals

- 修复“剧本生成解析失败 → fallback 到 mock_service → 内容重复/单场景/不合格”的根因。
- 让剧本 regenerate 产出结构化、多场景、非 mock 的脚本内容。
- 补齐单测、跑后端 quick gate、跑 prod build、Chrome E2E 验证，并更新 `tasks.md`。

## Changes

- `ai-pic-backend/app/services/episode_agent_episode_utils.py`: episode outline fallback 由 beats 生成 `plot_points/scenes`（最多 12），避免兜底只落 1 场景 summary。
- `ai-pic-backend/app/services/ai/scripts_ai_manager.py`: AI 管理器 direct 剧本生成显式传 `max_tokens`（场景规划/对白/修复），并在 JSON 解析失败时走一次“只输出严格 JSON”的修复轮次，降低 MiniMax 默认 256 tokens 截断导致的解析失败与 mock 回退。
- `ai-pic-backend/app/services/ai/scripts.py`: LangGraph Script Agent 增加 120s 超时保护；无 `scene_budgets` 时默认传 `duration_minutes=0`（跳过时长预算/REACT），超时后自动回退 direct 生成。
- `ai-pic-backend/tests/unit/services/test_episode_agent_episode_utils.py`: 覆盖 beats→scenes/plot_points 与上限裁剪。
- `ai-pic-backend/tests/unit/services/ai/test_scripts_ai_manager.py`: 覆盖 direct 生成的 `max_tokens` 透传与 repair 调用。
- `ai-pic-backend/tests/unit/services/ai/test_scripts_generation_mixin.py`: 覆盖 Script Agent 超时后回退 direct。
- `tasks.md`: 新增并标记“剧本生成稳定性（避免 mock 回退）”修复条目。

## Validation

- Tests: `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Build: `./docker/build_prod_images.sh`
- Chrome E2E:
  - 登录 `http://localhost:8089/login`（账号 `geyunfei`）。
  - 打开 `http://localhost:8089/episodes/1cca3cc61d7740b4b5f73bccf8fe4d32/workspace` → 剧本 → 点击“重新生成剧本”并确认。
  - 刷新后选择新剧本 `v1.1 (Script ID: 83)`，确认页面展示 7 个场景、对白/舞台指令非空。
  - 后端校验：`GET /api/v1/scripts/83` 显示 `ai_model=ai_manager_minimax` 且 `scene_count=7`。

## Next Steps

- 前端：regenerate 成功后自动切换到新 scriptId（当前需要刷新/手动选择）。
- 继续做“文生图/图生图提示词语义与 provider 参数一致性”全局审计，并按 provider 能力进一步优化模板与动态表单（拆分原子提交）。

## Linked Commits

- (pending)
