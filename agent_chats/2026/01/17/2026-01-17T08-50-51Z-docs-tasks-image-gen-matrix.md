---
id: 2026-01-17T08-50-51Z-docs-tasks-image-gen-matrix
date: 2026-01-17T08:50:51Z
participants: [human, codex]
models: [gpt-5.2]
tags: [docs, tasks, image-gen, provider-aware]
related_paths:
  - docs/image-gen-provider-matrix.md
  - docs/README.md
  - tasks.md
summary: "Document provider-aware image-gen prompt semantics and provider×mode matrix; update tasks board accordingly."
---

## User Prompt

全局检查文生图/图生图提示词规范与 provider 参数一致性；并检查/更新 `tasks.md`。

## Goals

- 为文生图/图生图统一出一份可对照的提示词语义与 provider×mode 参数矩阵，避免“UI 展示了但提交被忽略”
- 同步更新 `tasks.md`，将本轮 provider-aware 工作进度可追踪化

## Changes

- `docs/image-gen-provider-matrix.md`: 新增 provider-aware 图像生成提示词语义说明与能力矩阵（以 `supported_ai_manager_keys()` 为准），补充 Virtual IP / Environment / Storyboard 的差异化策略说明。
- `docs/README.md`: 将新增文档加入 docs 索引。
- `tasks.md`: 标记本轮完成项（negative_prompt/reference_images 降级、Storyboard refs 策略、分镜图生图弹窗模型提示/单参考图限制），并补充矩阵文档链接。

## Validation

- `./docker/build_prod_images.sh`

## Next Steps

- 按 provider 补齐更多“参数范围/默认值”文档（如 volcengine guidance_scale 范围、keling fidelity 推荐值），并把 UI 文案与校验补齐到图生图弹窗

## Linked Commits

- (pending)
