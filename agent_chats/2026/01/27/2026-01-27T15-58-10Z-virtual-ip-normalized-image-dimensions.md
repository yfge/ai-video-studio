---
id: 2026-01-27T15-58-10Z-virtual-ip-normalized-image-dimensions
date: 2026-01-27T15:58:10Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, virtual-ip, image-gen, audit]
related_paths:
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation_helpers.py
  - ai-pic-backend/tests/unit/services/ai/test_images_generation_mixin.py
  - ai-pic-backend/tests/unit/test_virtual_ip_image_task_normalized_params.py
  - tasks.md
summary: "Persist normalized size/width/height/aspect_ratio for VirtualIP txt2img results and validate via unit tests + Chrome."
---

## User Prompt

把 P0 都处理：优先补齐虚拟 IP 文生图的归一化尺寸落库（`size/width/height/aspect_ratio`），确保审计与筛选一致。

## Goals

- VirtualIP 文生图：在 `VirtualIPImage.generation_params` 中落盘 **normalized** 的 `size/width/height/aspect_ratio`。
- 兼容旧结果结构（缺字段时回退），并避免 OSS 字段为 `None` 时的异常。
- 增加单测覆盖，并用真实浏览器路径验证落库结果。

## Changes

- `ai-pic-backend/app/services/ai/images_generation.py`：`generate_virtual_ip_image` 返回值补充 `size/aspect_ratio/width/height`（来自 `normalize_image_gen_request`）。
- `ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py`：\n+  - 优先使用 result 中的 normalized 值写入 `generation_params`（即使为 `None` 也记录）。\n+  - 补齐 `width/height` 落库。\n+  - 修复 `oss_upload=None` 时 `.get()` 报错（安全取值）。\n+  - 同步把 normalized 值写入 task 产出的 image metadata（便于排查）。\n+- `ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation_helpers.py`：同步兼容同样的 normalized params 组装与 OSS 安全取值。
- 测试：\n+  - `ai-pic-backend/tests/unit/services/ai/test_images_generation_mixin.py` 增加对返回 normalized 尺寸/宽高的断言。\n+  - 新增 `ai-pic-backend/tests/unit/test_virtual_ip_image_task_normalized_params.py`，覆盖 Celery worker 写库时以 result 的 normalized 值为准（例如 `2K` → `1024x1024`）。\n+- 看板：`tasks.md` 勾选“虚拟 IP 文生图落盘 normalized 尺寸信息”完成。

## Validation

- Pytest（pre-commit quick gate）：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`。
- Chrome E2E（真实链路）：\n+  - 登录 `geyunfei` → 打开虚拟 IP “老拐”（`/virtual-ip/2335...`）。\n+  - 通过浏览器调用 `POST /api/v1/virtual-ips/1/images/generate-async`（`size=2K, model=dalle-3`）创建任务 `task_id=5850`。\n+  - 轮询 `GET /api/v1/tasks/5850` 直到 `completed`，返回 `result_file_path=virtual_ip_image:1:88`。\n+  - 校验 `GET /api/v1/virtual-ips/1/images` 中 `id=88` 的 `generation_params`：`size=1024x1024, width=1024, height=1024, aspect_ratio=null`（确认使用 normalized 值）。\n+
## Next Steps

- P0：继续补齐软删 + `business_id` 的 pytest/E2E 验证，并核查是否存在未统一到 Task 队列的生成入口。

## Linked Commits

- (current) 同提交。

