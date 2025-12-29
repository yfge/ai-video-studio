---
id: 2025-12-29T07-36-52Z-script-dialogue-react-fill-guard
date: 2025-12-29T07:36:52Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, script, duration]
related_paths:
  - ai-pic-backend/app/services/script_agent_react_fill.py
  - ai-pic-backend/app/prompts/templates/script_dialogues.txt
  - ai-pic-backend/app/prompts/templates/script_word_count_constraint.txt
  - ai-pic-backend/tests/unit/services/test_script_agent_react_fill.py
summary: "Prevent REACT dialogue fill from accepting under-duration outputs; tighten dialogue prompts for scene_number correctness and no robot-like filler."
---

## User Prompt

现在从剧本→对白→分镜的流程时间轴对不齐（对白过少、音频过短）。需要在剧本层面精确控制对白，并修正对白里不合理/像助手回复的内容。

## Goals

1. 防止 REACT 兜底补全在“不达标”时仍写回脚本，导致对白更短/更乱。
2. 强化对白生成提示词：scene_number 必须准确、覆盖所有场景、禁止“明白/收到/继续执行”等机器人式台词。
3. 用单测锁住兜底逻辑，避免回归。

## Changes

1. `ai-pic-backend/app/services/script_agent_react_fill.py`
   - 仅当补全结果满足“最小时长/最大时长”约束时才返回 merged 结果；否则返回 `None`（避免把不达标的补全写回脚本）。
2. `ai-pic-backend/app/prompts/templates/script_dialogues.txt`
   - 增强对白输出约束：覆盖所有场景、scene_number 必须为整数且准确、对白条数按字数/时长目标自动决定。
   - 明确禁止机器人/任务执行风格台词，减少“阿盖儿：明白，我们继续”类不合理对白。
3. `ai-pic-backend/app/prompts/templates/script_word_count_constraint.txt`
   - 增加 per-scene 的 scene_number 强约束（必须为当前场景编号）。
4. `ai-pic-backend/tests/unit/services/test_script_agent_react_fill.py`
   - 调整既有用例以满足新的“达标才返回”逻辑。
   - 新增用例：当多次补全仍不达标时应返回 `None`，且会重试 3 次。

## Validation

1. Pytest（目标单测）
   - `cd ai-pic-backend && pytest -q tests/unit/services/test_script_agent_react_fill.py`
2. Docker 生产镜像构建
   - `./docker/build_prod_images.sh`（成功；脚本按 `git rev-parse --short HEAD` 打 tag，因此使用了当时的 `HEAD=6e25ae5`，工作区仍有未提交变更，存在 tag 与内容不完全一致的风险）
3. Chrome E2E（本地）
   - 登录：`geyunfei / Gyf@845261`
   - 入口：`http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script&scriptId=62`
   - 点击“重新生成剧本”→“确认重新生成”，创建任务 `task_id=477`（脚本 62 重新生成）。
   - 观察 worker 日志中的 LLM Prompt Preview：已包含新增的“scene_number 必须准确”“禁止机器人式台词”等约束（确认提示词生效）。

## Next Steps

1. 修复前端“重新生成剧本”交互：当前接口返回的是任务创建（`task_id`），但 UI 弹“重新生成成功”并清空 script 视图（应改为提示“任务已提交”，并在任务完成后刷新脚本列表/自动切换到最新版本）。
2. 如果仍出现对白不足：考虑把 `script_agent` 的 per-scene 目标从“全场景时长”改为结合 `dialogue_ratio`/转场预算，避免过度苛刻导致频繁重试。
3. 跟进 `task_id=477` 卡住 PROCESSING 的问题（DB 的 `tasks.updated_at` 未刷新），排查 worker 任务完成后状态落库逻辑。

## Linked Commits

- (pending) 本次变更将随下一次提交更新

