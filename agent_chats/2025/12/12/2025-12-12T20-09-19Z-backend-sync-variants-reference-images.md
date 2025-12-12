---
id: 2025-12-12T20-09-19Z-backend-sync-variants-reference-images
date: 2025-12-12T20:09:19Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, img2img, environments, virtual-ip]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/tests/test_api.py
  - ai-pic-backend/tests/test_story_structure_endpoints.py
summary: "补齐环境/虚拟IP同步 variants 的 reference_images 透传，并添加回归测试"
---

## User Prompt

- 检查所有生图的地方看看还有没有漏掉的
- 现在的问题是，分镜的图生成没有传入参考图（已修复后继续排查其它入口）

## Goals

1. 环境/虚拟IP 的同步 variants 接口与异步版本保持一致：支持 `reference_images`。
2. 兼容前端传入相对路径（`/uploads/...`）的参考图，统一转换为可访问的绝对 URL。
3. 增加最小回归测试，避免后续再出现“透传丢失”。

## Changes

- 同步环境 variants：从 JSON body 读取 `reference_images`，将相对路径转换为 `INTERNAL_BACKEND_URL` 下的绝对 URL，并透传给 `image_to_image(extra_images=...)`（`ai-pic-backend/app/api/v1/endpoints/story_structure.py`）。
- 同步虚拟IP variants：同样补齐 `reference_images` → `extra_images`（`ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py`）。
- 回归测试：
  - 扩展 `test_generate_virtual_ip_image_variant`，断言同步 variants 会将 `reference_images` 透传为 `extra_images`（`ai-pic-backend/tests/test_api.py`）。
  - 新增 `test_environment_variants_pass_reference_images` 覆盖环境同步 variants（`ai-pic-backend/tests/test_story_structure_endpoints.py`）。

## Validation

- Backend：
  - `cd ai-pic-backend && pytest -q tests/test_api.py::TestVirtualIPAPI::test_generate_virtual_ip_image_variant`
  - `cd ai-pic-backend && pytest -q tests/test_story_structure_endpoints.py::test_environment_variants_pass_reference_images`
- Chrome E2E（本地 Dev 环境）：
  1. 登录测试账号 `geyunfei`（密码已脱敏）
  2. 在 `http://localhost:8089/environments` 通过 `fetch` 调用同步环境 variants（携带 `base_image` + `reference_images`），返回 200，且得到 `resource.lets-gpt.com` 的新图像 URL；页面显示「参考图」计数随之增加
  3. 通过 `fetch` 调用同步虚拟IP variants（携带 `reference_images`），返回 200 并创建新的变体图片记录

## Next Steps

1. 如需统一入口，可考虑在通用 `generate/image-to-image` 请求 schema 中补齐 `reference_images`（再由后端统一映射到 `extra_images`）。
2. 继续清点其它“旧同步接口”是否仍存在透传缺口，避免新旧路径行为不一致。

## Linked Commits

待提交：fix(backend): pass reference_images in sync variants
