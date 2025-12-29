---
id: 2025-12-29T03-46-40Z-model-ui-merge-ratio-resolution
date: 2025-12-29T03:46:40Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, backend, ui, video, google]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider/video.py
  - ai-pic-backend/tests/unit/test_google_provider_video.py
  - ai-pic-frontend/src/components/shared/ImageModelUiFields.tsx
  - ai-pic-frontend/src/components/shared/VideoModelAdvancedFields.tsx
  - ai-pic-frontend/src/components/shared/VideoModelUiFields.tsx
summary: "Merge aspect ratio + size/resolution controls, and accept `ratio` for Google Veo video generation."
---

## User Prompt

在选择参考图片生成视频的部分，如果选了 google 的 image=preview 即使选了宽高比，还是会被分辨率覆盖掉；所有的生图的地方去掉这个分辨率单独输入的设置，和宽高比合并；注意检查 docs/api 中每一个模型的不同，做到前后端一致。

## Goals

- 让 Google Veo 视频生成正确读取前端传入的 `ratio`（避免被 `aspectRatio` 命名差异吞掉）。
- 将“宽高比 + 分辨率/尺寸”在 UI 上合并为单一选择，避免用户分别设置导致的覆盖/不一致。

## Changes

- Backend: `ai-pic-backend/app/services/providers/google_provider/video.py` 支持将 `ratio` 作为 `aspectRatio` 的别名进行解析（与内部 API 字段对齐）。
- Backend tests: `ai-pic-backend/tests/unit/test_google_provider_video.py` 增加单测，断言请求 body 的 `parameters.aspectRatio` 会正确写入。
- Frontend: `ai-pic-frontend/src/components/shared/ImageModelUiFields.tsx` 当模型同时提供 `sizeOptions` 与 `aspectRatioOptions` 时，合并为 `画幅/尺寸` 单一选择器（如 `9:16 · 2K`）。
- Frontend: `ai-pic-frontend/src/components/shared/VideoModelUiFields.tsx` 合并 `画幅/分辨率` 单一选择器（如 `16:9 · 720P`），并在 model 切换时对非法/空值回落到默认值。
- Frontend: 新增 `ai-pic-frontend/src/components/shared/VideoModelAdvancedFields.tsx` 拆分水印/镜头控制等字段，保证单文件行数限制。

## Validation

- Backend: `cd ai-pic-backend && pytest -q tests/unit/test_google_provider_image.py tests/unit/test_google_provider_video.py`
- Frontend: `cd ai-pic-frontend && npm run lint`（存在既有 warning，lint 退出码为 0）
- Docker: `./docker/build_prod_images.sh`
- Chrome (MCP):
  - 打开 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/storyboard?scriptId=58`
  - 在“生成视频（第 4 帧）”弹窗中确认出现 `画幅/分辨率` 合并选择器
  - 在“选择参考图生成关键帧”弹窗切换到 `Gemini 3 Pro Image Preview — Google`，确认出现 `画幅/尺寸` 合并选择器（例如 `1:1 · 1K`）

## Next Steps

- 继续对齐各 provider 的 `metadata.ui`（options/默认值）与 `docs/api/*`，确保 UI 仅展示真实支持的组合。
- 将“返回剧集页”从 `/episodes/[id]` 入口改为 `/episodes/[id]/workspace?tab=storyboard&scriptId=...`（单独原子提交）。

## Linked Commits

- (pending)

