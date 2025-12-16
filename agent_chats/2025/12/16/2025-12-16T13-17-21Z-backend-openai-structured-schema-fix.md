---
id: 2025-12-16T13-17-21Z-backend-openai-structured-schema-fix
date: 2025-12-16T13:17:21Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, openai, schema, script]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-backend/tests/unit/test_openai_schema_fix.py
  - tasks.md
summary: "Fix OpenAI structured outputs schema validation error for script_dialogues by typing item schemas and adding strict fallback."
---

## User Prompt

OpenAI 文本生成报错：`response_format 'script_dialogues'` schema 校验 400（required/properties 不符合 structured outputs 严格要求），导致流式与非流式都失败。

## Goals

- 避免 OpenAI `response_format=json_schema` 因 schema 不兼容直接 400，保证脚本对白生成可继续执行。
- 保持对 structured outputs 的支持：schema 满足 strict 规则时继续使用 strict；不满足时自动降级到 `json_object`。

## Changes

- `ai-pic-backend/app/services/script_agent.py`：`script_dialogues` 的 `dialogues/stage_directions` items 增加明确的字段 `properties`（scene_number/character/content/emotion/action 等），避免 generic object 在 strict 下不兼容。
- `ai-pic-backend/app/services/ai_service.py`：同步补齐 `_call_ai_manager_script` 的 `script_dialogues` schema（含 scenes items 的基础字段）。
- `ai-pic-backend/app/services/providers/openai_provider.py`：新增 `_is_openai_strict_schema` 检测；schema 不满足 strict 约束时自动回退到 `response_format=json_object`，避免 400。
- `ai-pic-backend/tests/unit/test_openai_schema_fix.py`：新增 strict-schema 检测单测覆盖（generic object items 被拒、typed items 被接受）。
- `tasks.md`：记录并勾选该修复项。

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_openai_schema_fix.py`

## Next Steps

- 若仍遇到 OpenAI schema 400，记录当次 `response_format.json_schema.schema`（脱敏）与模型 id，以便补齐 strict 规则差异。

## Linked Commits

- pending
