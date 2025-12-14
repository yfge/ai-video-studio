---
id: 2025-12-14T15-08-36Z-filter-reference-images
date: 2025-12-14T15:08:36Z
participants: [human, codex]
models: [gpt-4o]
tags: [backend, image-generation, reference-images]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Filter invalid reference image strings to avoid 404 preloads when building extra_images"
---
## User Prompt
- 线上环境出现“莫名其妙的图片地址”如 `STYLE_SPEC => ...`，并有 404 请求 (ai-video-backend:8000/实验室全景参考图1 等) 在图生图预加载阶段。

## Goals
- 避免将非 URL 的描述性字符串当作参考图去下载，减少 404 和提示词内容被误当作 URL 的情况。

## Changes
- 添加参考图过滤助手 `_normalize_reference_images`：仅保留 http(s)/data:image 或带常见图片后缀的路径，其它文本直接忽略。
- 在虚拟 IP 图像变体/图生图和环境图变体/图生图的 extra_images 构建时使用该过滤逻辑，防止将描述性中文词条转换为 backend 基础域名导致 404。

## Validation
- `pytest tests/test_tasks_minimal.py -q`。

## Next Steps
- 在线上复现场景检查 image_to_image 预加载日志是否仍出现中文描述 URL；如仍有遗漏，可扩大过滤规则（例如仅允许带协议/后缀的 URL）。

## Linked Commits
- fix(backend): filter invalid reference images
