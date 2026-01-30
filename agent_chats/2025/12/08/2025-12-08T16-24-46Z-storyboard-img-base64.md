---
id: 2025-12-08T16-24-46Z-storyboard-img-base64
date: 2025-12-08T16:24:46Z
participants: [human, codex]
models: [gpt-4o]
tags: [backend, frontend, storyboard, image-generation]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Handle multi-reference storyboard image generation by preloading refs as base64, improve polling/UX, and verify in Chrome."
---

## User Prompt

分镜管理中参考图生成失败，检查模型输入（参考图需转 base64），并增强图像生成体验。要求用 Chrome 自测并查看后端日志。

## Goals

- 让图生图调用能使用多张参考图（含人物、环境），后端能读到内网上传的图片。
- 前端提供自动轮询/状态提示，能看到生成结果。
- 用 Chrome 自测生成过程并记录后端日志。

## Changes

- Backend: 预下载参考图（主图 + extra_images）转 data:image;base64 传给 provider；Volcengine/OpenAI provider 支持传入 base64_images，Volcengine 多图按 Seedream 限制 (≤14) 组装；修正 image_to_image 预加载使用默认超时配置。
- Frontend: 为分镜图像生成、批量生成和首尾帧生成添加轮询刷新提示，避免手动刷新；清理未用函数和依赖警告。

## Validation

- `docker exec ai-video-frontend npm run lint` (通过，已有 <img> 警告仍在)。
- `docker exec ai-video-backend pytest`（全量因缺少 selenium 依赖与既有 SyntaxError 失败）；`docker exec ai-video-backend pytest tests/test_tasks_minimal.py` 通过。
- Chrome 自测：http://localhost:8089/episodes/8/storyboard 登录后，重选场景环境=办公室、角色=老拐/文闻，使用“选择参考图生成”在帧7、帧2触发多参考图生成；轮询提示出现，预览更新，帧7/帧2 获得新的 Seedream 图像链接。
- 后端日志：生成请求体包含多张 /uploads/\*，image_to_image 预加载改为 base64（无 timeout 属性告警后成功），Volcengine seedream-4.5 image_to_image 返回 200 并写入新 URL。

## Next Steps

- 若需消除现有 ESLint `<img>` 警告，需后续用 `<Image />` 替换。
- 后端全量 pytest 需安装 selenium 并修复 tests/unit/test_openai_unit.py 现有 SyntaxError。

## Linked Commits

- (pending)
