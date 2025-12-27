---
id: 2025-12-27T18-44-22Z-fix-script-dialogue-fill
date: "2025-12-27T18:44:22Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, scripts, langgraph, react, dialogue]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/app/services/script_agent_react_fill.py
  - ai-pic-backend/app/services/script_missing_parts.py
  - ai-pic-backend/app/services/script/script_generator.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/regenerate.py
  - ai-pic-backend/app/core/celery_app.py
  - ai-pic-backend/tests/conftest.py
  - ai-pic-backend/tests/unit/services/test_script_agent_word_count.py
  - ai-pic-backend/tests/unit/services/test_script_missing_parts.py
  - ai-pic-backend/tests/unit/test_episode_agent_callbacks.py
  - ai-pic-backend/tests/unit/test_episode_step_outline_light.py
summary: "修复剧本对白缺失导致的占位对白问题：REACT 兜底补全缺失场景对白，并避免写入误导性占位对白。"
---

## User Prompt

用户反馈“从剧本→对白→分镜时间轴对不齐”，并指出 `scriptId=51` 出现明显不对的占位对白；要求先看现有 agents 设计，并用 Chrome 在指定 episode/workspace URL 做验证回归。

## Goals

- 解决“对白缺失/过少时写入通用占位对白”的问题，避免用户看到明显不对的内容。
- 在剧本生成链路中增加更鲁棒的 REACT/兜底策略：当多次重试仍缺失对白时，改为按缺失场景定向补全。
- 保持下游（对白音轨/时间轴/分镜）不被空内容阻断。

## Changes

- `ScriptLangGraphAgent`：
  - `_estimate_dialogue_duration` 对 `scene_number` 做 int 归一，避免字符串编号导致误判为 0s。
  - 在 `react_max_retries_reached` 分支增加“仅对 PENDING 场景补全对白/舞台指示”的最后兜底调用，并将结果合并回整体对白列表（写入 reasoning：`react_filled_pending_scenes([...])`）。
  - 将该兜底逻辑抽到 `script_agent_react_fill.py`，避免继续膨胀 `script_agent.py`。
- 缺失内容兜底：
  - 新增 `app/services/script_missing_parts.py`，提供 `populate_dialogues_and_stage_if_missing`：对白缺失时写入与场景 summary 一致的旁白（而不是通用占位对白），舞台指示缺失时写入 action 占位，避免误导。
  - `scripts_legacy._populate_dialogues_and_stage_if_missing` 改为调用该服务函数（保持兼容签名）。
  - `ScriptGenerator` 改为直接调用该服务函数，避免从 endpoint 导入带来的耦合。
- 其他：
  - `_enforce_storyboard_variety` 同步更新 `ai_prompt` 前缀以匹配变体 description（修复单测期望）。
  - `celery_app` 在 pytest 环境使用 `memory://` broker + `cache+memory://` backend，并启用 eager，避免测试连接外部 Redis。
  - 为测试 fixture 补齐/修正必要 monkeypatch（`scripts_legacy.ai_service` 等），并让 episode agent 的 callback 单测不再触发 duration REACT 循环（`episode_duration=None`）。
  - 增加/更新单测覆盖：缺失对白兜底与对白时长估算鲁棒性。

## Validation

- Backend quick gate：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（通过）。
- Docker：执行 `./docker/build_prod_images.sh`（通过）。
- Chrome（MCP）E2E：
  - 打开 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script&scriptId=51`，确认 v1.7 场景 1 出现通用占位对白（复现）。
  - 点击“重新生成剧本”→“确认重新生成”，等待 Celery 任务完成后生成新剧本 `v1.8 (ID: 52)`。
  - 访问 `...&scriptId=52`，确认场景 1-3 不再出现“等一下……让我再确认一下/明白，我们继续”通用占位对白；reasoning 中出现 `react_filled_pending_scenes([1, 2, 3])`。

## Next Steps

- 考虑将“旁白型兜底对白”在音轨生成时标记/过滤，避免兜底旁白被当作真实对白生成 TTS（如果产品侧不希望旁白出声）。
- 前端工作台在异步 regenerate 时增加任务状态展示，避免出现短暂的 “- ID:” 选择器状态。

## Linked Commits

- (pending)
