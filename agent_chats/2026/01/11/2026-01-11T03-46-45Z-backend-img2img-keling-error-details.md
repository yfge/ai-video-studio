---
id: 2026-01-11T03-46-45Z-backend-img2img-keling-error-details
date: "2026-01-11T03:46:45Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image, img2img, keling, fix]
related_paths:
  - ai-pic-backend/app/services/ai/images_providers.py
  - ai-pic-backend/app/services/ai/model_ui.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/image/image_providers.py
  - ai-pic-backend/app/services/image_gen/refs.py
  - ai-pic-backend/app/services/providers/image_param_utils.py
  - ai-pic-backend/app/services/providers/keling_provider/image.py
  - ai-pic-backend/app/services/providers/keling_provider/models.py
  - ai-pic-backend/app/services/providers/keling_provider/provider.py
  - ai-pic-backend/tests/unit/services/image_gen/test_refs.py
  - ai-pic-backend/tests/unit/test_keling_provider_image_to_image.py
summary: "Fix VirtualIP img2img failures by normalizing Keling inputs and surfacing provider errors instead of generic messages"
---

## User Prompt

修复“所有图生图提供商都失败了”这个错误（重点在虚拟 IP 图生图），并统一梳理后端行为。

## Goals

- 让虚拟 IP 图生图失败时返回可行动的 provider 错误（而不是泛化“全都失败了”）。
- 修复 Keling（可灵）图生图请求中参考图格式不兼容导致的失败。
- 保证 Celery worker 容器内可访问参考图（localhost URL 在容器内不可达）。

## Changes

- Keling provider：对传入的 `data:*;base64,` 参考图做拆包，仅传递纯 base64 字符串给可灵接口，避免 `code=1201 File is not in a valid base64 format`。
- `AIServiceManager.generate_image()`：记录并回传最后一次失败的真实错误（provider/model/error），避免只返回“所有图像生成提供商都失败了”。
- `AIServiceManager.image_to_image()`：在全部图生图通路失败时回传最后一次真实错误（此前已做），并配合上面的 `generate_image()` 兜底不再丢失错误细节。
- 参考图 URL：将 `localhost/127.0.0.1/0.0.0.0` 重写为 `backend_base`，确保 worker 能下载并 base64 预加载。
- Keling 模型：修正无效的旧 model id（`kling-image-*`）到可用的 `kling-*`，并增加兼容映射。
- 补充单元测试覆盖 `refs` URL 重写与 Keling img2img 行为。

## Validation

- Backend tests: `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Docker: `docker compose -f docker/docker-compose.dev.yml restart ai-video-celery-worker`
- Chrome E2E (MCP):
  - 登录 `geyunfei` / `Gyf@845261`
  - 进入 `http://localhost:8089/virtual-ip/233525e9045146d580a1d18ef4a28161#ip-images`
  - 点击任一图片的“图生图”→ 选择“可灵”→ 选择“可灵图像生成 V2.1”→ 提交
  - 进入 `/tasks`，最新任务错误信息展示为可灵返回的具体原因（例如 `Keling image generation HTTP 429: ... Account balance not enough`），不再是“所有图生图提供商都失败了”。

## Next Steps

- 进一步确认可灵哪些模型/接口真实支持 image-to-image（当前 `kling-v2-1` 返回不支持 img2img 的错误），并在模型能力/下拉选项中做约束，避免用户选择必失败组合。
- 若需要严格图生图一致性：可考虑在图生图失败时不要自动降级为文生图，或在任务详情中同时展示“图生图失败原因 + 文生图兜底原因”。

## Linked Commits

- (pending) fix(backend): surface keling img2img errors
