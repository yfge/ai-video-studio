---
id: 2025-12-13T12-47-01Z-style-spec-tests
date: 2025-12-13T12:47:01Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tests, style]
related_paths:
  - ai-pic-backend/app/utils/style_utils.py
  - ai-pic-backend/tests/unit/test_ai_service_manager_style_spec.py
  - ai-pic-backend/tests/unit/test_style_utils.py
summary: "Added unit tests for StyleSpec resolution and prompt injection; fixed StyleSpec prompt to render enum values."
---

## User Prompt

为新的 StyleSpec 统一风格链路补齐更完整测试，减少对外部服务的依赖，并确保 provider 的 style 映射与 prompt 拼装稳定可用。

## Goals

- 增加单元测试覆盖：StyleSpec resolve 合并逻辑、prompt 注入、OpenAI style 映射与 metadata 回填。
- 修复测试暴露的 prompt 渲染问题（避免输出 Enum repr）。

## Changes

- 修复 `build_style_prompt()`：使用 `model_dump(mode="json")` 输出枚举值字符串，避免 `StyleUniverse.JAPANESE_ANIME` 这类 Enum repr 进入 prompt。
- 新增单元测试：
  - `test_style_utils.py`：覆盖 defaults/preset/legacy 解析、prompt 输出、legacy/openai style 推导。
  - `test_ai_service_manager_style_spec.py`：用 recording provider 验证 prompt 注入、OpenAI `style` 参数、以及 `AIResponse.metadata.style_spec` 回填。

## Validation

- `cd ai-pic-backend && ruff check app/utils/style_utils.py tests/unit/test_style_utils.py tests/unit/test_ai_service_manager_style_spec.py`
- `cd ai-pic-backend && black --check app/utils/style_utils.py tests/unit/test_style_utils.py tests/unit/test_ai_service_manager_style_spec.py`
- `cd ai-pic-backend && pytest -q tests/unit/test_style_utils.py tests/unit/test_ai_service_manager_style_spec.py`

## Next Steps

- 前端接入 presets/schema 后，补一条 Chrome E2E 覆盖「选择 preset → 触发生成 → 后端落库/metadata 可见」。
- 如需更细分的 provider style 参数（非 OpenAI），继续扩展映射并补对应单测。

## Linked Commits

- test(backend): add style spec unit coverage
