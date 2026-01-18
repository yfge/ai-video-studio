---
id: 2026-01-18T04-40-13Z-volcengine-img2img-count
date: 2026-01-18T04:40:13Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, provider, volcengine, image_gen]
related_paths:
  - ai-pic-backend/app/services/providers/volcengine_provider/provider.py
summary: "Fix Volcengine img2img count parameter mapping"
---

## User Prompt

全局检查文生图/图生图提示词规范，并优化所有 provider 参数一致性，按原子化提交推进。

## Goals

- 修复 Volcengine/Seedream 图生图在多张生成时 `count` 未生效的问题

## Changes

- `VolcengineProvider.image_to_image()` 支持 `n`（AIServiceManager 传入）并映射到内部 `count`

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- Chrome (MCP): 登录 `http://localhost:8089/login` → 进入 `http://localhost:8089/tasks` 确认页面可用

## Next Steps

- 统一文生图/图生图的 reference images 能力矩阵（重点：keling 文生图参考图映射、keling 图生图多参考限制）
- 在 UI 元数据中补充 provider 级提示（如 Google 413 风险）

## Linked Commits

- (pending)
