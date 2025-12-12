---
id: 2025-12-12T20-11-36Z-backend-oss-cdn-upload-log
date: 2025-12-12T20:11:36Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, oss, logging, cdn]
related_paths:
  - ai-pic-backend/app/services/storage/oss_service.py
summary: "OSS 上传成功时输出 CDN/URL 关键信息，方便确认生图是否走 CDN"
---

## User Prompt

- ip文生图没有走 CDN？把 CDN 上传加到日志里

## Goals

1. 当 OSS 上传成功时，在 worker 日志中明确输出 `object_key` 与最终 `url`，便于排查“是否走 CDN/OSS”。
2. 不改变上传行为，仅补充可观测性。

## Changes

- 在 `OSSService.upload_file_content` 上传成功分支补充 INFO 日志：`CDN 上传成功 | object_key=... url=... bytes=... prefix=...`（`ai-pic-backend/app/services/storage/oss_service.py`）。

## Validation

- Backend：
  - `cd ai-pic-backend && python -m compileall app/services/storage/oss_service.py`
  - `cd ai-pic-backend && pytest -q tests/integration/test_oss.py`
- Chrome E2E（本地 Dev 环境）：
  - 在环境页与虚拟IP variants 生成流程中，接口返回的新图片 URL 为 `resource.lets-gpt.com/...`（作为“已上传到 OSS/CDN 可访问域名”的侧证；具体上传日志由本次改动补齐到 worker 输出）。

## Next Steps

1. 若需要更精确区分“OSS 源站 vs CDN 域名”，可在配置中显式区分 `ALIYUN_OSS_DOMAIN`（CDN 域名）与 `endpoint`，并在日志中同时输出两者。

## Linked Commits

待提交：chore(backend): log CDN upload success in oss service
