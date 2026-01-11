---
id: 2026-01-11T07-42-24Z-backend-image-storage-dict-url
date: "2026-01-11T07:42:24Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, images, storage, bugfix]
related_paths:
  - ai-pic-backend/app/services/ai/images_storage.py
  - ai-pic-backend/tests/unit/services/ai/test_images_storage_mixin.py
summary: "Handle dict-shaped image_url payloads during image persistence"
---

## User Prompt

- 修复“所有图生图提供商都失败了”这个错误，并重新验证（已充值）。
- 修复环境图像持久化阶段报错：`image_url={'index': 0, 'url': '...'}` 导致 `'dict' object has no attribute 'startswith'`。

## Goals

- 让图像下载/持久化对 provider 返回的 `image_url` 结构更健壮（字符串 URL / data URL / dict 包装）。
- 避免因持久化崩溃导致错误归因到“所有提供商都失败”。
- 增加回归测试覆盖该输入形态。

## Changes

- 更新 `ImageStorageMixin._download_image()`：当 `image_data` 为 dict 时，自动从 `url/image_url/image/src` 提取字符串 URL；无法解析则抛 `TypeError`。
- 新增单测覆盖 dict 包装的 `data:image/...` 输入，确保可落盘并返回本地路径。

## Validation

- 后端测试：
  - `cd ai-pic-backend && pytest tests/unit/services/ai/test_images_storage_mixin.py -q`
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（728 passed）
- Chrome 端到端：
  - 登录 `http://localhost:8089/login`（geyunfei）。
  - 进入环境详情 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`（env_id=7），选择「可灵 / 可灵图像生成 V2.1」发起环境文生图。
  - 任务页看到任务 `561` 状态为「已完成」，回到环境详情页引用图数量从 10 增加到 11，未再出现上述持久化报错。

## Next Steps

- 继续 Phase 2：在后端引入 provider+model 维度的 `generation_profile/preset` 默认参数，并前端统一选择/展示。

## Linked Commits

- (pending)
