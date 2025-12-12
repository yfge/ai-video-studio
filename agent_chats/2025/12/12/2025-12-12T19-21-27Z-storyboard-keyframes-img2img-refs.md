---
id: 2025-12-12T19-21-27Z-storyboard-keyframes-img2img-refs
date: 2025-12-12T19:21:27Z
participants: [human, codex]
models: [gpt-5.2]
tags: [storyboard, backend, frontend, img2img]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/unit/test_storyboard_keyframes_schema.py
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "分镜图生图支持首/尾关键帧，并压缩参考图以避免 Gemini 413 导致的无参考兜底"
---

## User Prompt

- 分镜的图生成没有传入参考图
- 最重要先打通「分镜首帧/尾帧 → 图生视频」最小链路

## Goals

1. 分镜图生图请求确保携带参考图，并真正用于生成（避免因为 413 等问题回落成“无参考”的文生图）。
2. 支持分镜单帧升级为首/尾关键帧（start/end）。
3. 前端分镜页支持小图完整显示与点击看大图。

## Changes

- 后端分镜图像生成增加 `keyframe_mode`：`start_end` 会为同一分镜生成首帧/尾帧并回填 `start_image_url`/`end_image_url`，同时保持 `image_url` 指向首帧兼容旧 UI（`ai-pic-backend/app/api/v1/endpoints/scripts.py`）。
- 分镜帧 schema 补齐 `start_image_url`/`end_image_url`（`ai-pic-backend/app/schemas/generation.py`）。
- Celery 任务入口透传 `keyframe_mode`，并补充 `storyboard_video_generate_task`（`ai-pic-backend/app/services/task_worker.py`）。
- 针对 Gemini/Google 图生图的请求体大小限制：在 `image_to_image` 的 base64 预加载阶段对参考图做“缩放+JPEG 重编码”，并根据是否偏好 Google 限制参考图数量，避免触发 413 进而回落到文生图（`ai-pic-backend/app/services/ai_service_manager.py`）。
- 前端分镜页默认以 `start_end` 方式生成，并展示首/尾关键帧缩略图；点击缩略图或「查看首/尾帧」打开大图预览（`ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`、`ai-pic-frontend/src/utils/api.ts`）。
- 增加单元测试覆盖 schema 兼容性（`ai-pic-backend/tests/unit/test_storyboard_keyframes_schema.py`）。

## Validation

- Frontend：`cd ai-pic-frontend && npm run lint`（通过；仓库内另有未改动文件的 warning）。
- Backend：`cd ai-pic-backend && pytest`（当前仓库测试基线存在大量失败/错误；本次新增的 `tests/unit/test_storyboard_keyframes_schema.py` 通过）。
- Chrome E2E（本地 Dev 环境）：
  1. 重启服务：`docker compose -f docker/docker-compose.dev.yml restart ai-video-backend ai-video-celery-worker`
  2. 登录测试账号 `geyunfei`（密码已脱敏）
  3. 打开 `http://localhost:8089/episodes/11/storyboard`，在分镜帧内点击「选择参考图生成关键帧」并提交（模型：Google / Gemini 2.0 Flash (image exp)）
  4. 后端任务参数与日志确认：`Task.id=184` 的 `parameters.frames=[3]` 且 `reference_images` 非空；Worker 日志出现 `LLM Response | task=image_to_image ... status=success`，并记录 `CDN 上传成功`（示例：`.../184558/e80772bc.png`、`.../184606/f5333396.png`）
  5. 页面刷新后可见分镜帧「关键帧预览」展示首/尾两张缩略图，且链接可打开对应 CDN URL

## Next Steps

1. 基于 `start_image_url/end_image_url` 接入图生视频（待配置实际 provider/key）。
2. 继续清点所有生图入口的参考图透传与 CDN 路径一致性（IP/环境/场景/分镜）。

## Linked Commits

待提交：分镜关键帧与参考图压缩修复
