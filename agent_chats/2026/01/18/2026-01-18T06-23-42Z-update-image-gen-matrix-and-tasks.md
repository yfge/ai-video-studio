---
id: 2026-01-18T06-23-42Z-update-image-gen-matrix-and-tasks
date: 2026-01-18T06:23:42Z
participants: [human, codex]
models: [gpt-5.2]
tags: [docs, tasks, image-gen]
related_paths:
  - docs/image-gen-provider-matrix.md
  - tasks.md
summary: "Updated provider-aware image-gen matrix with latest Google/Keling behavior and marked related tasks as done."
---

## User Prompt

检查并更新 `tasks.md`；全局检查文生图/图生图提示词与 provider 参数一致性，并补齐 provider×domain 兼容矩阵与验证记录。

## Goals

- 让 `docs/image-gen-provider-matrix.md` 真实反映当前 normalize/provider 行为（尤其是 Google 413、可灵 reference_images 映射）。
- 将本轮已完成的 provider-aware 事项同步回 `tasks.md`。

## Changes

- `docs/image-gen-provider-matrix.md`
  - 补充 Google/Gemini 文生图参考图 413 风险治理说明（最多 4 张 + 自动压缩）。
  - 修正可灵（Keling）文生图对 `reference_images` 的支持（仅 1 张，映射到 `image`，并在有参考图时合并 `negative_prompt`）。
  - 增加 Chrome 快速核验场景（Environment/Storyboard）。
- `tasks.md`
  - 标记完成：Google/Gemini 413 风险治理、分镜文生图 reference_images 动态输入、provider×domain 矩阵与 E2E 验证项。

## Validation

- Prod build: `./docker/build_prod_images.sh`
- 本提交仅涉及文档/任务看板；功能验证与关键请求截图已在对应功能提交的 `agent_chats` 中记录。

## Next Steps

- 将“max_reference_images”（按 provider+mode）做成结构化 UI 元数据，前端用它限制选择数量（keling=1、google=4）。

## Linked Commits

- chore(docs): update image gen provider matrix

