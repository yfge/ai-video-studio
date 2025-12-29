---
id: 2025-12-29T02-51-36Z-script-dialogue-duration-calibration
date: "2025-12-29T02:51:36Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, script, duration]
related_paths:
  - ai-pic-backend/app/prompts/templates/script_word_count_constraint.txt
  - ai-pic-backend/app/services/duration_orchestrator/constants.py
  - ai-pic-backend/app/services/duration_orchestrator/nodes/tts_trial.py
  - ai-pic-backend/app/services/duration_orchestrator/utils.py
  - ai-pic-backend/app/services/script_agent_react_fill.py
  - ai-pic-backend/tests/unit/services/duration_orchestrator/test_assemble_episode.py
  - ai-pic-backend/tests/unit/services/duration_orchestrator/test_budget_allocation.py
  - ai-pic-backend/tests/unit/services/duration_orchestrator/test_tts_trial.py
  - docs/design/duration-orchestrator-agent.md
summary: "Calibrated script dialogue duration estimation to match production TTS rate and strengthened REACT fill guards."
---

## User Prompt

剧本 → 对白 → 分镜/时间轴链路出现“对白过少、音频过短、时间轴对不齐”。用户要求在剧本层面更精确控制对白时长/字数，并用 docker 的 MySQL 数据检查现状，最后用 Chrome 在 `episode workspace`（scriptId=51）验证回归。

## Goals

- 用线上数据校准对白“字/秒”估算，减少剧本阶段对白字数偏少导致的后续时间轴漂移。
- 在 REACT 兜底补全阶段对每个场景对白时长做检查，确保尽量贴近场景预算区间。
- 同步更新相关提示词/文档/单测，避免前后不一致。

## Changes

- 用 MySQL `scene_beats`（`beat_type='dialogue'`）统计校准 `WORDS_PER_SECOND_*`，将默认语速提升到 `4.7` 字/秒（≈282 字/分钟），并相应调整 slow/fast 档位。
- 更新剧本字数约束提示词与文档示例：从 135 字/分钟改为 280 字/分钟口径。
- 调整 duration-orchestrator 的建议生成逻辑：改为基于 `WORDS_PER_SECOND` 估算增删字数。
- 强化 `try_fill_pending_scenes_after_react`：
  - 补全尝试次数从 2 次提升到 3 次；
  - 在“每场景至少 2 句对白”基础上，新增按 `SceneBudget.min/max_duration_seconds` 的对白时长估算校验；不达标会追加 REACT 驳回提示，要求扩写/删减并禁止编剧/助手元语言与跨场景重复模板台词。
- 更新相关单测断言以匹配新语速基线。

## Validation

- MySQL（docker）：
  - `SELECT ROUND(SUM(CHAR_LENGTH(dialogue_excerpt))/SUM(duration_seconds),4) AS chars_per_sec ... FROM scene_beats WHERE beat_type='dialogue' ...;`
  - 结果：`chars_per_sec = 4.7052`（用于 `WORDS_PER_SECOND_NORMAL=4.7` 校准）。
- Backend：
  - `cd ai-pic-backend && pytest -q tests/unit/services/duration_orchestrator tests/scripts/test_script_dialogue_fallback.py`
- Docker：
  - `./docker/build_prod_images.sh`
- Chrome（MCP，自测回归）：
  - 登录：`geyunfei / Gyf@845261`
  - 打开：`/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script&scriptId=51`
  - 观察坏样本：场景 1 出现不合理对白（`阿盖儿: 明白，我们继续。`）。
  - 点击：`重新生成剧本` → `确认重新生成`
  - 观察生成后结果：页面自动切到新剧本（示例为 `ID: 61`），对白数量明显提升（如 scene1=6、scene4=17），且不再出现“明白，我们继续”这种跨场景模板对白。

## Next Steps

- 将“对白时长/字数达标”从“兜底补全”提升为“生成强约束”：若场景对白时长仍明显不足则让生成失败并提示重试原因（避免落库劣质剧本）。
- 继续回归：用改进后的剧本生成时间轴与分镜，验证整体对齐（对白音频长度与场景预算一致）。
- 处理前端问题：修正从分镜管理返回的入口路由、统一生图参数（移除分辨率手填并与宽高比合并，按 docs/api 做前后端一致）。

## Linked Commits

- (paired with the commit that adds this entry)
