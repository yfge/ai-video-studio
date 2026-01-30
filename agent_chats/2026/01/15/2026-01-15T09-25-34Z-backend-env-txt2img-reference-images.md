---
id: 2026-01-15T09-25-34Z-backend-env-txt2img-reference-images
date: 2026-01-15T09:25:34Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, story-structure, image-gen]
related_paths:
  - ai-pic-backend/app/services/story_structure/environment_image_requests.py
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/tests/unit/services/story_structure/test_environment_image_requests.py
  - ai-pic-backend/tests/unit/services/story_structure/test_environment_image_generation_reference_images.py
summary: "Support reference_images for environment txt2img requests"
---

## User Prompt

按 provider 动态加载输入以获得额外信息；并优化所有 provider/域的参数一致性（含文生图 reference_images），原子化分布提交。

## Goals

- 环境文生图（sync/async）支持接收 `reference_images`，并把它们透传到统一的 image-gen 归一化与 provider 参数层。
- 保证相对路径 reference_images 在后端可归一化为绝对 URL（避免 dropped/unnormalized）。

## Changes

- `EnvironmentTextToImageRequest` 新增 `reference_images` 字段，并在 `resolve_environment_text_to_image_request()` 解析/透传。
- `build_environment_text_to_image_task_payload()` 在存在 reference_images 时写入 Celery payload。
- `generate_environment_images()` 构造 `ImageGenRequest` 时补齐 `reference_images` + `backend_base`，使归一化后可进入 provider 调用（支持的 provider 才会保留该参数）。
- 新增单测覆盖 request/payload 与 env txt2img 生成时 `reference_images` 进入 provider call。

## Validation

- `cd ai-pic-backend && pytest -q tests/unit/services/story_structure/test_environment_image_requests.py tests/unit/services/story_structure/test_environment_image_generation_reference_images.py`
- `./docker/build_prod_images.sh`
- Chrome (MCP):
  - 打开 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`
  - DevTools Console 发起 `POST /api/v1/story-structure/environments/.../images/generate-async`，body 含 `reference_images`
  - DevTools Network: `POST /api/v1/story-structure/environments/.../images/generate-async` (reqid=866, 200) Request Body 中包含 `reference_images`，响应返回 `task_id=591`。

## Next Steps

- 前端：在环境「AI 生成参考图」表单中提供参考图选择器，并按所选 model 的 `supportsExtraImages` 动态显示/提交 `reference_images`。
- 后端：将同类 txt2img reference_images 输入扩展到其它 domain（如虚拟 IP / storyboard）需要时再接入。

## Linked Commits

- (pending)
