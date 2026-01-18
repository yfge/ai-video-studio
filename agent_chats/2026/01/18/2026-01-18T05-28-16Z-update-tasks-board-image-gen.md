---
id: 2026-01-18T05-28-16Z-update-tasks-board-image-gen
date: 2026-01-18T05:28:16Z
participants: [human, codex]
models: [gpt-5.2]
tags: [process, tasks, image_gen]
related_paths:
  - tasks.md
summary: "Update tasks board for provider-aware image generation work"
---

## User Prompt

检查并更新 `tasks.md`，同步当前文生图/图生图 prompt 与 provider 参数对齐工作的进度与下一步。

## Goals

- 把本轮已完成的 provider-aware 生图改动同步到任务看板
- 补充下一步待做项（Google 413、provider×domain 矩阵、分镜文生图动态输入）

## Changes

- `tasks.md`：在「图像生成提示词/参数规范化（provider-aware）」章节新增/更新条目，标记已完成项并补充待办

## Validation

- `./docker/build_prod_images.sh`
- 目视检查 `tasks.md` 勾选状态与章节结构

## Next Steps

- 完成 `docs/image-gen-provider-matrix.md` 并补齐 Chrome E2E 用例记录
- 治理 Google/Gemini `reference_images` 413（限制/压缩/提示/后端降级策略）

## Linked Commits

- (pending)
