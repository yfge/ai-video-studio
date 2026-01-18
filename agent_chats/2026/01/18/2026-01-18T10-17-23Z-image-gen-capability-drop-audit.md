---
id: 2026-01-18T10-17-23Z-image-gen-capability-drop-audit
date: 2026-01-18T10:17:23Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen]
related_paths:
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/image_gen/normalize_capabilities.py
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize_capability_drops.py
  - docs/image-gen-provider-matrix.md
  - tasks.md
summary: "在 normalize 阶段按 provider+mode(+model) 丢弃不支持参数并写入 audit_warnings，避免 silent drop。"
---

## User Prompt

全局检查文生图/图生图提示词规范与 provider 参数一致性；按 provider 进一步优化；原子化分布提交并更新 tasks.md。

## Goals

- 避免 `seed/steps/cfg_scale/strength/style_preset_id/style_spec` 等参数在不支持的 provider 上被静默过滤。
- 让 UI/元数据里展示的“最终使用参数”与实际下发一致，且能通过 `audit_warnings` 追踪“被忽略”的原因。

## Changes

- 新增 `apply_capability_drops()`：基于 `supported_ai_manager_keys()`（并对 Volcengine `cfg_scale` 做 model 级校验）丢弃不支持参数，写入 `audit.warnings` + `audit.dropped_fields`。
- `normalize_image_gen_request()` 在返回前调用 capability drops，确保 normalized 元数据与 `build_ai_manager_call()` 下发一致。
- 新增单测覆盖：OpenAI 丢弃 seed/steps/cfg_scale、Volcengine(Seedream4.5) 丢弃 cfg_scale、Keling img2img 丢弃 strength、OpenAI 丢弃 style_spec/style_preset_id。
- 更新 `docs/image-gen-provider-matrix.md` 与 `tasks.md` 记录该行为。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`（提交前后各执行一次以对齐 tag）
- Chrome E2E：环境详情页切换火山模型，确认 Seedream 3.0 t2i 显示 cfg_scale 相关提示，而 Seedream 4.5 不显示；并确认页面“环境文生图提示”区域可展示 `audit_warnings`。

## Next Steps

- 前端在切换模型/provider 时清理不支持的高级参数（避免提交旧值），并将后端 audit 信息在更多入口可视化。
- 补齐其它 provider/model 的细粒度能力判定（如更多 volcengine 模型 gating）。

## Linked Commits

- (pending)

