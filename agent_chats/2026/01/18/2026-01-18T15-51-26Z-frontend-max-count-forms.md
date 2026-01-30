---
id: 2026-01-18T15-51-26Z-frontend-max-count-forms
date: "2026-01-18T15:51:26Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, image-gen, ui]
related_paths:
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationOptionsFields.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/VirtualIPImageManager.tsx
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImageSettingsForm.tsx
  - ai-pic-frontend/src/utils/modelUi.ts
  - tasks.md
summary: "前端按 provider-aware max_count 动态限制文生图/图生图生成张数，避免提交无效的 count 参数。"
---

## User Prompt

- 优化所有 provider 和域；选择不同 provider 时动态加载输入以得到额外信息；原子化分布提交。

## Goals

- 前端根据后端 `image_gen` UI 元数据的 `max_count` 动态限制“生成张数”，并在切换模型/provider 时自动裁剪超限输入。

## Changes

- `modelUi.extractImageGenUi()` 解析后端 `max_count` 并暴露为 `maxCount`。
- 虚拟 IP 文生图：`生成数量` 下拉选项按 `maxCount` 动态生成，并展示「一次最多 N 张」提示；切换模型时自动将 `count` 裁剪到上限。
- 环境文生图：同样按 `maxCount` 动态限制 `count`，并展示提示。
- 图生图弹窗：提交/输入侧按 `maxCount` clamp，避免提交不支持的 batch count。
- `tasks.md` 勾选前端 `max_count` 进度项。

## Validation

- `cd ai-pic-frontend && npm run lint`
- `./docker/build_prod_images.sh`
- Chrome（localhost:8089）：
  - 登录 `geyunfei` 后进入虚拟 IP「老拐」图片管理，点击「AI 生成图片」，确认 `生成数量` 仅显示 `1 张`，并显示提示「一次最多 1 张」。
  - 打开任意「图生图」弹窗，确认 `生成张数` 输入上限为 1（`max=1`）并展示相同提示。

## Next Steps

- 后端：补齐「虚拟 IP 文生图落盘 normalized spec」并统一 count clamp（与 audit_warnings）。
- 提示词：全局审计各 domain 的 txt2img/img2img 模板语义与 provider 参数一致性，并据此完善 UI 元数据（字段支持/限制/建议）。

## Linked Commits

- TBD
