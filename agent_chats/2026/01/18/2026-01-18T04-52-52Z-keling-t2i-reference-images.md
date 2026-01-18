---
id: 2026-01-18T04-52-52Z-keling-t2i-reference-images
date: 2026-01-18T04:52:52Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image_gen, provider, keling]
related_paths:
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/app/services/image_gen/ui_metadata.py
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize.py
  - ai-pic-backend/tests/unit/services/image_gen/test_provider_params_reference_images.py
  - ai-pic-backend/tests/unit/services/image_gen/test_ui_metadata_reference_images.py
summary: "Enable Keling txt2img reference_images mapping and add UI hints"
---

## User Prompt

全局检查文生图/图生图提示词规范、对齐 provider 参数，并在选择不同 provider 时动态加载输入/提示信息。

## Goals

- 让可灵（Keling）文生图在携带 `reference_images` 时可真正下发到 provider（映射到 `image`）
- 明确可灵文生图在“有参考图”时的 `negative_prompt` 行为，避免参数静默失效

## Changes

- `ImageGenRequest(TEXT_TO_IMAGE)`：当 provider 支持 `image` 时允许 `reference_images` 进入归一化流程
- 可灵文生图：当提供 `reference_images` 时
  - 仅保留第一张参考图
  - 将 `negative_prompt` 合并进 prompt 并清空 `negative_prompt`
- `build_ai_manager_call()`：可灵文生图把 `reference_images[0]` 映射为 `image`
- UI 元数据：为可灵文生图追加提示语（参考图仅 1 张、negative_prompt 合并策略）
- 新增/更新单测覆盖上述规则

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- Chrome (MCP): 打开 `http://localhost:8089/environments/aab17f172446462a97e738772337d272` → 切换 provider 到「可灵」→ 页面展示“可灵文生图参考图仅支持 1 张…”提示

## Next Steps

- 前端虚拟 IP 文生图模型列表修复（当前错误拉取 ImageToImage models）
- Google/Gemini 参考图 413 风险治理（压缩/限制张数/后端提示）

## Linked Commits

- (pending)
