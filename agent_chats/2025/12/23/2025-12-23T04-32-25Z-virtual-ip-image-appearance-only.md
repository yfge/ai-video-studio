---
id: 2025-12-23T04-32-25Z-virtual-ip-image-appearance-only
date: 2025-12-23T04:32:25Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, virtual-ip, refactor]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation_helpers.py
summary: "[refactor] Limit virtual IP image generation prompts to appearance-only fields"
---

## User Prompt

IP图像生成不传人物小传等内容，只传形象部分。

## Goals

- 图像生成仅使用角色形象/风格相关字段。
- 将虚拟IP图像生成端点逻辑拆分到辅助模块以满足文件/函数规范。

## Changes

- 抽出虚拟IP图像生成辅助函数与持久化逻辑，缩短 endpoint 实现。
- 生成描述改为仅使用角色描述与风格提示词（不再拼接背景故事/人物小传）。

## Validation

- `pytest` (ai-pic-backend) — failed with multiple existing failures.
- `./docker/build_prod_images.sh` — success.
- MCP/Chrome: opened `http://localhost:8089/virtual-ip` → 502 Bad Gateway, unable to run UI flow.

## Next Steps

- 恢复本地 Web 服务后，走一次虚拟IP图像生成端到端流程。
- 排查并修复现有 pytest 失败项。

## Linked Commits

- TBD
