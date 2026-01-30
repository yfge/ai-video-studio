---
id: 2026-01-19T23-38-23Z-backend-google-veo-oss-polling
date: 2026-01-19T23:38:23Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, video, google, veo, oss, fix]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider/models_video.py
  - ai-pic-backend/app/services/providers/google_provider/video.py
  - ai-pic-backend/app/services/providers/google_provider/video_helpers.py
  - ai-pic-backend/app/services/providers/google_provider/video_tasks.py
  - ai-pic-backend/app/services/storage/oss_admin_mixin.py
  - ai-pic-backend/app/services/storage/oss_backup_mixin.py
  - ai-pic-backend/app/services/storage/oss_service.py
  - ai-pic-backend/app/services/storage/oss_upload_mixin.py
  - ai-pic-backend/app/services/video/video_task_polling_logging.py
  - ai-pic-backend/app/services/video/video_task_polling_service.py
  - ai-pic-backend/tests/unit/services/video/test_video_task_polling_service.py
  - ai-pic-backend/tests/unit/test_google_provider_video_tasks.py
summary: "修复 Google Veo 视频参数约束与 OSS 上传可靠性，并补齐 video polling 的 download_url"
---

## User Prompt

全流程测试短剧制作（DeepSeek 文生文、Google Image 文生图、Google Veo 生视频），发现视频生成/下载链路不稳定且报错信息不足，需要修复并能在浏览器里验证。

## Goals

- 修正 Veo 模型在分辨率/时长上的硬约束，避免无效参数导致任务失败
- 让视频生成的 HTTP 错误信息可追踪（状态码/响应体），便于定位 4xx/5xx/限流
- 轮询任务返回结果时保留 `download_url`，前端能查看/下载原始视频
- OSS 下载/上传链路更鲁棒（支持重定向、视频更长超时、统一 `.mp4` 扩展名）

## Changes

- `ai-pic-backend/app/services/providers/google_provider/video_helpers.py`: 新增 `format_http_status_error()` 并对 Veo 时长进行分辨率约束归一化
- `ai-pic-backend/app/services/providers/google_provider/models_video.py`: 补充 Veo 3.1 的 `duration_options_by_resolution` 元数据
- `ai-pic-backend/app/services/providers/google_provider/video.py`, `ai-pic-backend/app/services/providers/google_provider/video_tasks.py`: 捕获 `httpx.HTTPStatusError` 并输出更完整错误详情
- `ai-pic-backend/app/services/video/video_task_polling_service.py`: 轮询构建响应时补回 `download_url`；日志拆分到 `ai-pic-backend/app/services/video/video_task_polling_logging.py`
- `ai-pic-backend/app/services/storage/oss_service.py`: 按职责拆分为薄封装；新增 `oss_*_mixin.py`，并在下载时启用 `follow_redirects`、视频更长超时、默认补齐 `.mp4`
- `ai-pic-backend/tests/unit/test_google_provider_video_tasks.py`: 覆盖 Veo 分辨率/时长归一化逻辑
- `ai-pic-backend/tests/unit/services/video/test_video_task_polling_service.py`: 覆盖 polling 响应包含 `download_url`

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- Chrome（本地）：登录 `geyunfei`，打开分镜页 `http://localhost:8089/episodes/d7339307de354edbae078817fba303c4/storyboard?scriptId=107`，确认已生成帧包含「查看/下载视频」链接；并在数据库中确认 `scripts.extra_metadata.storyboard.frames[0..4].video_url` 为 `resource.lets-gpt.com/.../*.mp4`

## Next Steps

- 修复视频任务 fallback 报错被“所有提供商都失败了”掩盖的问题，保留真实 provider 错误
- 继续补齐第 1 集剩余分镜视频（frame 5–9），并逐个下载抽检
- 排查/补齐剧集“时间轴”生成链路（分镜页提示需先在剧集页生成）

## Linked Commits

- fix(backend): harden google veo video + oss upload + polling
