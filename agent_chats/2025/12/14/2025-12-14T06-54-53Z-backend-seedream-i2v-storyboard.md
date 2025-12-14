---
id: 2025-12-14T06-54-53Z-backend-seedream-i2v-storyboard
date: 2025-12-14T06:54:53Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, storyboard, video, volcengine, seedream, oss]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/unit/test_generate_video_provider_model.py
  - ai-pic-backend/tests/unit/test_model_listing.py
  - ai-pic-backend/tests/unit/test_storyboard_keyframes_schema.py
  - docs/api/volcengine-video.md
summary: "Add Seedream/Volcengine image-to-video pipeline for storyboard frames, including start/end frame inputs and OSS uploads for generated videos."
---

## User Prompt
检查火山引擎首尾帧图生视频并完成：分镜页展示、统一上传 OSS；并改为“用已有首尾帧生成视频”。随后要求：实现 Seedream 图生视频（分镜管理弹 modal，模型仅 Seedream 且参数对齐；任务完成上传 OSS；分镜管理可播放视频）。

## Goals
- 支持“首帧/首尾帧 → 图生视频”的后端任务链路与数据回填。
- 视频生成结果（视频/封面/尾帧）统一上传 OSS，并回写到分镜帧。
- 模型列表支持 `image_to_video` 类型筛选，并提供 Seedream 图生视频别名模型。

## Changes
- 实现 Volcengine Ark Video Generation（Seedance）异步任务创建 + 轮询，支持 `first_frame/last_frame` 输入并回传 `video_url/thumbnail_url/last_frame_url`。
- `AIService.generate_video` 默认 `return_last_frame=true`，并将视频/封面/尾帧统一走 `oss_service.upload_from_url` 上传 OSS，返回 OSS URL + original URL。
- 分镜视频异步任务支持按帧选择 `start_image_url/end_image_url`，并回写到 storyboard frame 的 `video_url/video_thumbnail_url/video_last_frame_url` 及 `video_generation` 元信息。
- 模型列表增强：支持 `model_type=image_to_video`，并在 Volcengine provider 中提供 `seedream-i2v-*` 别名模型（内部映射到 Seedance Ark 模型）。

## Validation
- Backend unit tests: `pytest -q tests/unit/test_model_listing.py tests/unit/test_generate_video_provider_model.py tests/unit/test_storyboard_keyframes_schema.py`
- Chrome (MCP) smoke check: 打开 `http://localhost:8089/episodes/10/storyboard`，确认关键帧（首/尾）预览可见且“生成视频”弹窗可打开；该页面似乎来自旧构建，未能在浏览器中看到最新 Seedream-only 模型筛选（需要重启/重新构建前端服务后再复验）。

## Next Steps
- 在实际环境（带可用 ARK/OSS 配置）跑一次真实“首尾帧 → 图生视频”生成，确认任务完成后回写 OSS URL，分镜页可播放。
- 若 Ark 拉取参考图受限，补充输入图自动转 OSS 并使用 OSS URL 作为输入的兜底策略。

## Linked Commits
- (pending)

