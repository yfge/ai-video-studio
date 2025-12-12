---
id: 2025-12-12T11-41-04Z-add-cdn-upload-logging
date: 2025-12-12T11:41:04Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, logging, oss]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
summary: "在图像持久化时记录 CDN 上传结果，便于确认虚拟IP文生图是否经过 OSS/CDN"
---

## User Prompt

ip文生图没有走 CDN？rithm=TOS4-HMAC-SHA256&X-Tos-Credential=AKLTYWJkZTExNjA1ZDUyNDc3YzhjNTM5OGIyNjBhNDcyOTQ%2F20251212%2Fcn-beijing%2Ftos%2Frequest&X-Tos-Date=20251212T113412Z&X-Tos-Expires=86400&X-Tos-Signature=f82ddf0661b88dd868f45d4ef37287e3059699e43e7bc3b1c1c0ee577942ba77&X-Tos-SignedHeaders=host']} ... 把 CND 上传加到日志里

## Goals

1. 补充日志以确认虚拟IP文生图在持久化时是否触发 CDN/OSS 上传。
2. 在未配置或上传失败回落到本地路径时也能直观看到原因。

## Changes

- 在 `ai-pic-backend/app/services/ai_service.py` 的 `_persist_local_image` 中记录 CDN 上传成功的 object_key、URL 与前缀；当上传未返回可用 URL 或 OSS 未配置时输出告警/提示，便于追踪是否实际走 CDN。

## Validation

- `pytest tests/test_api.py::TestVirtualIPAPI::test_generate_virtual_ip_image -q`（失败：接口返回 404，可能与本地测试数据或路由加载相关；本次仅改动日志未调整接口）
- 未进行 Chrome 端到端验证：当前环境未启动前后端服务，变更仅涉及日志输出

## Next Steps

- 进一步排查 `virtual-ips/{id}/generate-image` 在本地环境 404 的原因，补齐可运行的集成验证路径。

## Linked Commits

待提交：记录 CDN 上传日志
