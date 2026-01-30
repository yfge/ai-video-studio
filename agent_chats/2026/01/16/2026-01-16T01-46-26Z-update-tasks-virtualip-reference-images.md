---
id: 2026-01-16T01-46-26Z-update-tasks-virtualip-reference-images
date: 2026-01-16T01:46:26Z
participants: [human, codex]
models: [gpt-5.2]
tags: [docs, tasks, image-gen]
related_paths:
  - tasks.md
summary: "更新 tasks.md：标记虚拟IP文生图 reference_images 已完成"
---

## User Prompt

检查和更新 `tasks.md`。

## Goals

- 让任务板与最新实现保持同步（provider-aware `reference_images` 扩展到虚拟 IP 文生图）

## Changes

- `tasks.md`：在“图像生成提示词/参数规范化（provider-aware）”进度中标记虚拟 IP 文生图 `reference_images` 的后端/前端完成项，并拆分剩余分镜入口 TODO

## Validation

- Docker: `./docker/build_prod_images.sh`
- Chrome E2E: N/A（仅更新任务板）

## Next Steps

- 完成分镜文生图的 `reference_images` 动态输入与端到端验证，并补齐 provider×domain 兼容矩阵

## Linked Commits

- (pending)
