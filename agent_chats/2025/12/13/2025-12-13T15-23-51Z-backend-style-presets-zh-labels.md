---
id: 2025-12-13T15-23-51Z-backend-style-presets-zh-labels
date: "2025-12-13T15:23:51Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, style, i18n]
related_paths:
  - ai-pic-backend/app/utils/style_utils.py
  - ai-pic-backend/app/api/v1/endpoints/styles.py
  - ai-pic-backend/tests/unit/test_style_utils.py
summary: "Style schema/presets endpoints now return Chinese labels for UI display."
---

## User Prompt

检查所有的风格预设，后端返回的接口要有中文（英文不利于产品使用）。

## Goals

- `/api/v1/styles/schema` 的枚举 options 返回可读中文 `label`
- `/api/v1/styles/presets` 的预设返回中文 `label/description`
- 保持 `value/preset_id` 不变（便于前端/存储/兼容）

## Changes

- `ai-pic-backend/app/utils/style_utils.py`
  - 新增 13 维枚举值到中文 `label` 的统一映射（后端作为唯一真源）。
  - `build_style_schema_options()` 生成 options 时优先使用中文 label（无映射则回退到原有 humanize）。
  - 将内置 `STYLE_PRESETS` 的 `label/description` 改为中文可读文案。
- `ai-pic-backend/app/api/v1/endpoints/styles.py`
  - `GET /api/v1/styles/presets/{preset_id}` 404 detail 改为中文。
- `ai-pic-backend/tests/unit/test_style_utils.py`
  - 增加单测：schema options 与 presets 的中文输出校验。

## Validation

- Pytest (targeted):
  - `cd ai-pic-backend && pytest tests/unit/test_style_utils.py`
- API sanity (localhost):
  - 登录拿 token 后调用：
    - `GET http://localhost:8000/api/v1/styles/schema` 确认 `style_universe`/`color_mood` 等 option.label 为中文（如 `日系动漫`）。
    - `GET http://localhost:8000/api/v1/styles/presets` 确认 `label/description` 为中文（如 `默认漫画`）。
- Chrome E2E (localhost:8089):
  - 登录账号 `geyunfei`
  - 打开 `http://localhost:8089/virtual-ip/1/images` → 点击「🤖 AI生成图像」
  - 验证「风格预设」下拉展示中文（如 `默认漫画/赛博朋克·霓虹`）
  - 展开「高级风格」面板，验证各维度下拉 option 展示中文（如 `日系动漫/国漫`）

## Next Steps

- 如需多语言支持，可在 schema 中增加 `label_i18n`（或按 `Accept-Language` 返回不同 label）。
- 逐步把任务详情/资产详情里的 `style_spec` 展示改为“value + 中文 label”的组合展示（避免直接展示 raw value）。

## Linked Commits

- fix(backend): localize style schema and presets
