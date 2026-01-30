---
id: 2026-01-12T09-14-07Z-backend-image-url-normalization
date: 2026-01-12T09:14:07Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, bugfix, image-gen]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/tests/unit/test_ai_service_manager_image_payload_normalization.py
summary: "Normalize provider image payloads to prevent dict-to-string persistence crashes (startswith on dict)."
---

## User Prompt

- 修复 “所有图生图提供商都失败了 / 环境图像持久化失败” 相关问题；日志中出现 `{'index': 0, 'url': ...}: 'dict' object has no attribute 'startswith'`。

## Goals

- 确保 AI provider 返回的 `images` 列表在下游持久化前统一规范为 `list[str]` URL。
- 避免 dict/非字符串 image payload 传入下载/上传逻辑导致 `startswith` 崩溃。
- 增加最小回归测试覆盖该 payload 形态。

## Changes

- `ai_service_manager.py`：在 `_convert_base64_images_to_oss()` 内统一归一化 `images` 输入（支持 list/单值、dict 包含 `url`/`image_url`），并保证输出始终为 `list[str]`。
- `test_ai_service_manager_image_payload_normalization.py`：新增单测，覆盖 images 为 `[{index,url}, {url}, "url"]` 时可正确归一化。

## Validation

- Unit tests
  - `cd ai-pic-backend && pytest tests/unit/test_ai_service_manager_image_payload_normalization.py -q`
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome E2E (geyunfei / Gyf@845261)
  - 虚拟IP `老拐` → 图片管理 → 选任一图片点“图生图” → provider 选“可灵” → 提交 → 任务页确认 `task_id=577` 成功完成（不再出现 `'dict' object has no attribute 'startswith'`，result=`virtual_ip_image_variants:60:1`）。
- Docker prod build
  - `./docker/build_prod_images.sh` ✅

## Next Steps

- 将同类“images payload 形态归一化”进一步抽到通用 util，并在 provider 层统一约束（避免各处重复处理）。
- 继续修复/增强 “所有图生图提供商都失败了” 的错误聚合与可观测性（输出最后 provider+model+request_id）。

## Linked Commits

- (pending)
