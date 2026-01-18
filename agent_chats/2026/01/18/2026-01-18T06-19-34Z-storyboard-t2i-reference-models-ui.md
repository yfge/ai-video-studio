---
id: 2026-01-18T06-19-34Z-storyboard-t2i-reference-models-ui
date: 2026-01-18T06:19:34Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, storyboard, image-gen, ui]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImageSettingsForm.tsx
summary: "Enabled storyboard keyframe modal to use txt2img reference-image models (e.g. Volcengine) and switched GenerationProfileSelect/filtering based on mode."
---

## User Prompt

优化所有 provider 和域；参考现有形式，在选择不同 provider 时动态加载输入以得到额外信息；原子化分布提交；并将 reference_images 动态输入扩展到分镜文生图入口。

## Goals

- 分镜「选择参考图生成关键帧」弹窗支持 txt2img + reference_images 的模型（如火山 Seedream），不再只展示 img2img 能力模型。
- 质量档位（generation_profile）与文案跟随当前模式（text_to_image vs image_to_image）。
- 保持 UI 对“仅支持参考图文生图”的能力约束一致，减少误选。

## Changes

- `ImageToImageSettingsForm`：
  - 根据 `modelType` 自动选择 `genMode`（text_to_image / image_to_image）。
  - 模型过滤与 helperText 跟随模式：text_to_image 时仅保留支持 `reference_images` 的模型（基于 `image_gen` UI 元数据）。
  - `GenerationProfileSelect` 改为随模式请求 profiles（t2i 使用 steps/cfg/negative 的档位）。
- `ImageToImageModal`：当 `modelType` 为 text_to_image 时按钮文案改为「提交生成任务」。
- `episodes/[id]/storyboard/page.tsx`：分镜关键帧弹窗改用 `AIModelType.Image`（并更新 cacheKey），以展示支持 reference_images 的文生图模型。

## Validation

- Frontend lint: `cd ai-pic-frontend && npm run lint`（仅 warnings）
- Prod build: `./docker/build_prod_images.sh`
- Chrome (MCP) E2E:
  - 登录后打开 `http://localhost:8089/episodes/1cca3cc61d7740b4b5f73bccf8fe4d32/storyboard?scriptId=72`
  - 点击任一帧的「选择参考图生成关键帧」
  - 确认弹窗模型提供商列表包含「火山引擎」，且 helperText 显示“仅展示支持参考图文生图的模型”

## Next Steps

- 给 text_to_image refs 增加“最大参考图张数”元数据（keling=1、google=4 等），前端据此限制选择数量。
- 补齐 `docs/image-gen-provider-matrix.md` 并在 tasks.md 标记验证项。

## Linked Commits

- fix(frontend): enable storyboard t2i reference model picker
