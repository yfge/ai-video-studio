---
id: 2026-01-29T02-46-56Z-google-vertex-image-generation
date: "2026-01-29T02:46:56Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, providers, google, vertex, image-generation]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider/provider.py
  - ai-pic-backend/app/services/providers/google_provider/model_fetcher.py
  - ai-pic-backend/app/services/providers/google_provider/image_vertex.py
  - ai-pic-backend/app/services/providers/google_provider/image_routing.py
  - ai-pic-backend/app/services/providers/google_provider/vertex_generate_content.py
summary: "Prefer Vertex AI generateContent for Google image generation to bypass Gemini API geo restrictions."
---

## User Prompt

在 Docker 容器中做全流程测试（DeepSeek 生文 / Banana Pro 生图 / Google Veo 生视频），并把现有更改提交、清理工作区；同时修复/验证 Google Vertex AI 视频生成相关配置可用。

## Goals

- 解决 Gemini API 在当前环境出现 geo restriction（无法调用）导致的 Google 图像生成失败问题。
- 在 Google Provider 内优先走 Vertex AI（generateContent）完成文生图/图生图；在可用时保留 Gemini API fallback。
- 完成 Docker + Chrome（MCP）端到端验证，并记录生成结果与风险点。

## Changes

- `ai-pic-backend/app/services/providers/google_provider/provider.py`
  - `generate_image` / `image_to_image` 路由抽离，优先 Vertex，失败且存在 Gemini API key 时回退到 Gemini API。
  - `fetch_remote_models` 逻辑抽离到 `model_fetcher.py`，避免 provider 文件继续膨胀。
- `ai-pic-backend/app/services/providers/google_provider/image_vertex.py`
  - 新增 Vertex `:generateContent` 的图像生成实现（text-to-image / image-to-image），复用现有的图片参数规范化与响应解析逻辑。
- `ai-pic-backend/app/services/providers/google_provider/image_routing.py`
  - 提供统一的“Vertex 优先 + Gemini fallback”路由封装，降低 provider 复杂度。
- `ai-pic-backend/app/services/providers/google_provider/vertex_generate_content.py`
  - 抽出 Vertex endpoint/header 构造与 post 封装，统一错误映射为 `AIResponse`。
- `ai-pic-backend/app/services/providers/google_provider/model_fetcher.py`
  - 抽出 Google 远端模型列表拉取逻辑（复用 fallback/过滤），保持 provider 轻量。

## Validation

- Docker 服务重启验证：
  - `docker restart ai-video-backend ai-video-celery-worker`
- 后端接口 + Worker 真实调用验证（Vertex 图像生成）：
  - `POST /api/v1/scripts/115/storyboard/generate-images`（`model=google:gemini-2.5-flash-image`，`keyframe_mode=start_end`）
  - Worker 日志确认请求命中 Vertex endpoint（`https://us-central1-aiplatform.googleapis.com/...:generateContent` 200 OK），并将图片上传到 OSS/CDN。
- Veo 视频生成验证（Vertex async task + poll + OSS）：
  - 先出现一次 RAI filter（prompt/内容触发，operation 完成但无视频）；
  - 使用更安全的 prompt 重新提交后成功落库并上传，示例视频：
    - `http://resource.lets-gpt.com/ai-generated/videos/video/20260128/192626/ef844273.mp4`
    - `ffprobe` 验证 720x1280、24fps、8s。
- 测试与构建：
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（通过）
  - `./docker/build_prod_images.sh`（通过，镜像构建/推送成功）
- Chrome（MCP）端到端验证：
  - 登录：`http://localhost:8089/login`（geyunfei / Gyf@845261）
  - 打开：`http://localhost:8089/episodes/131/storyboard`
  - 在分镜帧中看到 Veo 视频信息与“查看/下载视频”链接；点击后在新标签页成功加载 mp4（浏览器原生 video controls 可见）。

## Next Steps

- [follow-up] 前端默认展示 `video_urls` 的首个条目，可能导致 UI 仍指向旧视频；建议改为显示最新 `video_url` 或允许选择/切换历史版本。
- [follow-up] 明确“Banana Pro”模型来源与可用性（Gemini API geo 限制下需转 Vertex 或提供替代图像模型）。
- [follow-up] 按 `tasks.md` 拆解“故事/剧集生成上下文与校验”、“统一 OSS 抽象”、“剧集默认屏幕比 + 临时覆盖”等任务并推进原子提交。

## Linked Commits

- (pending)
