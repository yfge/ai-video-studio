---
id: 2026-01-09T14-12-22Z-image-gen-normalization-phase2-virtual-ip-text2img
date: "2026-01-09T14:12:22Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, quality-consistency]
related_paths:
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/tests/unit/services/ai/test_images_generation_mixin.py
  - docs/design/image-generation-unification.md
summary: "Phase 2: route virtual IP text-to-image through normalization + runtime prompt for consistent quality."
---

## User Prompt

继续 Phase 2：统一梳理虚拟 IP / 环境 / 分镜 的图像生成链路，解释为什么没有统一提示词管理，并持续提升图片生成的质量一致性。

## Goals

- 让虚拟 IP 文生图（text-to-image）也走统一的 image-gen 归一化层，避免不同链路对同一参数（size/model/style）解释不一致。
- 把虚拟 IP 文生图提示词迁移到 PromptManager runtime 模板，降低提示词散落与漂移。
- 避免 style_spec prompt suffix 被重复叠加，提升风格一致性与可控性。
- 为关键行为补单测，并更新统一化设计文档。

## Changes

- `ai-pic-backend/app/services/ai/images_generation.py`：虚拟 IP 文生图接入 `app/services/image_gen` 归一化层（normalize + provider-safe call builder），并对 OpenAI DALL·E 路径做 size 归一化与 model alias（`dalle-*` → `dall-e-*`）兼容。
- 修复 style prompt 可能重复追加的问题：渲染 base prompt 时不直接追加 style_spec（交由归一化层/manager 处理），确保最终入参只追加一次。
- `ai-pic-backend/tests/unit/services/ai/test_images_generation_mixin.py`：新增单测覆盖（size 归一化 + style suffix 不重复；AIManager 路径使用 base prompt 且过滤 provider 不支持的 kwargs）。
- `docs/design/image-generation-unification.md`：更新 Phase 2/4 状态与 PromptManager 现状，补充本次迁移点。

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/ai/test_images_generation_mixin.py -q`
- `./docker/build_prod_images.sh`
- Chrome E2E（http://localhost:8089）：登录 `geyunfei`，在虚拟 IP「老拐」图片管理页打开「AI 生成图片」，选择 `volcengine:doubao-seedream-4-5-251128` / size=2K / 预设 `realistic_cinematic`，提交生成任务；在 `/tasks` 确认任务「虚拟IP文生图 - 老拐」Task ID=546 已完成，结果为 `virtual_ip_image:1:69`。

## Next Steps

- 跑 `pre-commit run` 并提交本次原子改动。
- 继续把其它链路（环境/分镜）PromptManager runtime prompt 彻底收拢到同一套模板注册与版本策略，形成“提示词资产化”闭环（可回滚/可对比/可审计）。

## Linked Commits

- (pending) refactor(backend): normalize virtual ip text2img
