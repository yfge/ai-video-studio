---
id: "2026-01-18T10-55-25Z-frontend-prune-image-gen-advanced"
date: "2026-01-18T10:55:25Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, image-gen, provider-aware]
related_paths:
  - ai-pic-frontend/src/components/shared/ImageGenAdvancedFields.tsx
  - tasks.md
summary: "Prune unsupported image-gen advanced params when switching models/providers."
---

## User Prompt

全局检查文生图/图生图提示词与参数规范，按 provider 动态加载输入并优化；原子化分布提交；检查并更新 tasks.md。

## Goals

- 在前端切换 provider/model 时，避免“隐藏字段仍携带旧值提交”的 silent mismatch。
- 保持表单 UI 与后端能力矩阵一致（不支持的字段不应被提交）。
- 按原子提交要求补齐 `agent_chats` 记录。

## Changes

- 新增按 `extractImageGenUi(model, mode)` 自动裁剪 `ImageGenAdvancedValue` 的逻辑：仅保留当前模型支持的字段（seed/steps/cfg_scale/negative_prompt/strength/image_reference/image_fidelity/human_fidelity）。
- 更新 `tasks.md`：标记“切换模型/provider 时自动清理不支持的高级参数”已完成。

## Validation

- `cd ai-pic-frontend && npm run lint` (0 errors)
- `./docker/build_prod_images.sh`
- Chrome E2E (MCP): 环境详情页 `http://localhost:8089/environments/5da63b15b5a640b380ef22cc30dc192b`
  - 登录 `geyunfei` / `Gyf@845261`
  - 选择模型 `volcengine:doubao-seedream-3-0-t2i-250415`，展开高级参数，设置 `cfg_scale=7`
  - 切换到 `volcengine:doubao-seedream-4-5-251128`（不支持 cfg_scale）后 `cfg_scale` 输入消失
  - 切回 `volcengine:doubao-seedream-3-0-t2i-250415` 后 `cfg_scale` 值已被清空

## Next Steps

- 将同样的“切换即清理”策略扩展到图生图弹窗的尺寸/比例等约束输入（避免旧值残留）。
- 继续全局审计提示词模板语义与 provider 参数映射（对齐 `docs/image-gen-provider-matrix.md`）。

## Linked Commits

- (this commit)
