---
id: 2025-12-28T06-41-01Z-script-dialogue-guardrails
date: 2025-12-28T06:41:01Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, script, react, validation]
related_paths:
  - ai-pic-backend/app/core/validators/__init__.py
  - ai-pic-backend/app/core/validators/script_dialogue_quality.py
  - ai-pic-backend/app/prompts/templates/script_dialogues.txt
  - ai-pic-backend/app/prompts/templates/script_review.txt
  - ai-pic-backend/app/prompts/templates/script_word_count_constraint.txt
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/app/services/script_agent_react_fill.py
  - ai-pic-backend/tests/unit/core/validators/test_script_dialogue_quality.py
  - ai-pic-backend/tests/unit/services/test_script_agent_react_fill.py
summary: "Add script-level dialogue guardrails to prevent underfilled scenes and meta writer notes, improving timeline alignment."
---

## User Prompt
现在从剧本→对白→分镜的流程里，时间轴对不齐（对白过少、音频过短）。同时现有剧本对白出现不合理内容（例如“阿盖儿：明白，这里可以突出冲突或情绪”这类编剧/助手元语言），希望在剧本层面加入更强的 REACT 检查与兜底，并用 MySQL 数据与 Chrome（workspace script tab）做验证回归。

## Goals
- 在剧本生成阶段强制对白数量与质量约束，减少“音频过短→时间轴漂移”。
- 禁止编剧/助手元语言进入对白。
- 识别并阻止跨场景重复的短模板台词（如多场景重复“明白，我们继续。”）。
- 修复 REACT 兜底补全的 JSON 解析与重试逻辑，避免 silently 失败。

## Changes
- 新增对白质量校验器：`app/core/validators/script_dialogue_quality.py`（writer note 检测、短台词复用检测、每场景最少句数校验）。
- 强化提示词约束：
  - `app/prompts/templates/script_dialogues.txt`：明确禁止元语言/重复模板台词，要求每场景 2-3 句对白且与 summary 强相关。
  - `app/prompts/templates/script_review.txt`：只做分类校正，遇到元语言必须删除或改写。
  - `app/prompts/templates/script_word_count_constraint.txt`：补充“禁止元语言”等硬约束。
- 强化 `ScriptLangGraphAgent`：
  - 场景字数预算按 `target_seconds * DIALOGUE_DENSITY_FACTOR * WORDS_PER_SECOND` 计算，避免 dialogue_ratio 导致目标字数趋近 0。
  - REACT 验证新增：每场景最少 2 句对白、writer note 检测、跨场景短台词复用检测；不通过则触发重试。
  - AI 返回为 dict 时直接使用，避免 `extract_json_block(str(dict))` 解析失败。
- 强化 REACT 最后兜底：`try_fill_pending_scenes_after_react` 支持 dict 直接解析，并最多 2 次重试以保证 pending 场景对白>=2 且无元语言。
- 新增/更新单测覆盖上述逻辑。

## Validation
- Pytest（quick gate）：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（669 passed）。
- Docker 生产镜像构建：`./docker/build_prod_images.sh`（成功，tag: `e34de0b`）。
- MySQL 数据验证：
  - 旧数据：`scripts.id=51` 场景 1/2/3 出现跨场景重复模板对白（“等一下……让我再确认一下。” / “明白，我们继续。”）。
  - 回归：通过异步“重新生成剧本”（task_id=466）得到 `scripts.id=57`（`ai_model=langgraph_script`），各场景对白条数：1=3、2=2、3=2、4=11；校验器检测 `writer_notes=0`、`reused_short_norms=[]`。
- Chrome E2E（MCP/DevTools）：
  - 登录：`geyunfei / Gyf@845261`
  - 打开：`http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script&scriptId=51`
  - 点击“重新生成剧本”，选择 `deepseek` + `deepseek-chat`，确认生成（POST `/api/v1/scripts/51/regenerate` → task 466）
  - 任务完成后打开：`http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script&scriptId=57`，确认场景 1-3 不再出现重复模板对白/元语言，并且每场景对白>=2。

## Next Steps
- 将同样的对白质量校验扩展到非 LangGraph 的 direct 生成分支（避免 script_agent 不可用时退化）。
- 增加“超短对白（如仅‘……’）”的约束或转为 pause beat，进一步减少“音频过短”风险。
- 修复前端对异步 regenerate 的处理（当前会插入 `- ID:` 占位项但不轮询 task 完成）。

## Linked Commits
- fix(backend): enforce script dialogue guardrails
