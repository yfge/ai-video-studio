---
id: 2026-01-14T15-23-54Z-image-gen-mode-scoped-notes
date: 2026-01-14T15:23:54Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, image-gen, providers]
related_paths:
  - ai-pic-backend/app/services/image_gen/ui_metadata.py
  - ai-pic-backend/tests/unit/services/test_model_ui_image_gen_metadata.py
  - ai-pic-frontend/src/utils/modelUi.ts
summary: "Scope provider capability notes to txt2img vs img2img"
---

## User Prompt

全局检查文生图/图生图提示词规范；模板语义是否正确；provider 参数一致性；可按 provider 动态加载额外输入；原子化分布提交。

## Goals

- UI 能按生成模式（text_to_image / image_to_image）展示正确的 provider 能力提示，避免“图生图专属提示”误出现在文生图表单。
- 为后续按 provider 动态加载额外输入字段打好元数据基础（mode-scoped notes）。

## Changes

- 后端：为 `text_to_image` / `image_to_image` 各自生成 `notes`（即使为空也返回），并按模式注入 provider 特定说明（如可灵 img2img 不支持 negative_prompt）。
- 前端：当 mode-scoped `notes` 存在时优先使用；否则回落到 legacy `imageGen.notes`，保证兼容旧后端。
- 测试：补充断言，确保可灵的 img2img-only 提示不会出现在 txt2img notes。

## Validation

- Chrome E2E（环境资产创建-文生图，已登录测试账号 `geyunfei`）：
  - 进入 `http://localhost:8089/environments` → 点击「创建环境资产」→ 勾选「创建后自动生成参考图」→ provider=可灵、model=可灵图像生成 V1 → 展开「高级参数」，确认不显示“可灵图生图不支持 negative_prompt”提示。
- 后端单测：`cd ai-pic-backend && pytest tests/unit/services/test_model_ui_image_gen_metadata.py -q`（通过）。
- 前端静态检查：`cd ai-pic-frontend && npm run lint`（通过，存在已知 warnings）。
- 生产镜像构建：`./docker/build_prod_images.sh`（通过）。

## Next Steps

- 将 img2img 高级参数（strength、image_reference/fidelity 等）逐域（Virtual IP、环境等）补齐并按 provider 能力动态显示。
- 对提示词模板做 provider 维度的“可用字段/推荐写法”整理，形成可复用规范文档与 UI 帮助文案。

## Linked Commits

- (this commit)
