---
id: 2026-01-10T15-15-07Z-fix-image-to-image-modal-type-export
date: "2026-01-10T15:15:07Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, build, fix]
related_paths:
  - ai-pic-frontend/src/components/shared/modals/index.ts
  - ai-pic-frontend/src/components/shared/modals/image-to-image/types.ts
summary: "修复 Next build：重新导出 LabeledReferenceImage 类型。"
---

## User Prompt

继续 Phase 2：前端统一选择与展示 generation_profile，并完成生产镜像构建校验。

## Goals

- 修复 `next build` 的类型导出错误，确保 `./docker/build_prod_images.sh` 可通过

## Changes

- 将 `LabeledReferenceImage` 的 re-export 从 `ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx` 调整为 `ai-pic-frontend/src/components/shared/modals/image-to-image/types.ts`

## Validation

- `pre-commit run`：待执行
- `./docker/build_prod_images.sh`：待执行（验证 frontend `next build` 不再因类型导出失败）

## Next Steps

- 完成本次修复的 pre-commit + docker prod build，通过后提交并更新上一个 ledger 的 Validation

## Linked Commits

- (pending)
