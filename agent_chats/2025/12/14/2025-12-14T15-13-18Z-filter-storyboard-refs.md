---
id: 2025-12-14T15-13-18Z-filter-storyboard-refs
date: 2025-12-14T15:13:18Z
participants: [human, codex]
models: [gpt-4o]
tags: [backend, storyboard, image-generation]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Filter storyboard reference images to avoid non-URL strings causing 404 preload"
---
## User Prompt
- 用户提供 curl 请求生成分镜图像，日志中仍出现非 URL 的参考图（如“实验室全景参考图1”）导致 404，且多出额外参考图请求。

## Goals
- 在分镜图像生成链路中过滤无效参考图字符串，避免将描述性文案拼接为 URL 参与预加载或入库。

## Changes
- 为分镜端点新增 `_normalize_reference_images`，仅保留 http/https/data:image 或带图片后缀的路径并转为绝对 URL。
- 框架、用户传入、环境参考图的列表在合并前统一过滤去重，存回帧引用并传给 image_to_image，防止生成阶段访问中文描述造成 404。

## Validation
- `pytest tests/test_tasks_minimal.py -q`。

## Next Steps
- 线上复现相同请求，检查日志是否仍出现中文描述 URL；若仍有遗漏可进一步收紧规则或记录具体字段来源。

## Linked Commits
- fix(backend): filter storyboard reference images
