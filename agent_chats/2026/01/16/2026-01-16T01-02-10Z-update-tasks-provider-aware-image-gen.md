---
id: 2026-01-16T01-02-10Z-update-tasks-provider-aware-image-gen
date: 2026-01-16T01:02:10Z
participants: [human, codex]
models: [gpt-5.2]
tags: [docs, tasks]
related_paths:
  - tasks.md
summary: "更新 tasks.md：补充 provider-aware 提示词/参数规范化任务并标记已完成项"
---

## User Prompt

检查和更新 `tasks.md`。

## Goals

- 将“文生图/图生图提示词规范 + provider 参数一致性”相关工作显式落到任务板
- 同步标记已完成的阶段性成果，避免遗漏

## Changes

- 在 `tasks.md` 增加“图像生成提示词/参数规范化（provider-aware）”特性条目与进度清单
- 在“场景/环境资产与分镜联动”中补充并标记环境文生图 `reference_images` 的后端/前端完成项

## Validation

- Docker: `./docker/build_prod_images.sh`

## Next Steps

- 扩展 `reference_images` 动态输入到虚拟 IP 文生图/分镜文生图等入口，并补齐 provider×domain 兼容矩阵与 Chrome 端到端验证记录

## Linked Commits

- (pending)
