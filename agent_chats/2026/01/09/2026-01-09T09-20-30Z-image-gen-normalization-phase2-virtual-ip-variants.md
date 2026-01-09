---
id: 2026-01-09T09-20-30Z-image-gen-normalization-phase2-virtual-ip-variants
date: "2026-01-09T09:20:30Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image, refactor]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/variants.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_variant_task.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/__init__.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_service.py
  - ai-pic-backend/app/services/image_gen/coerce.py
  - ai-pic-backend/tests/test_api.py
summary: "Phase 2: wire image-gen normalization into Virtual IP img2img (sync + async) and validate via Chrome E2E"
---

## User Prompt

用户确认继续 Phase 2：将“图像生成归一化层”接入虚拟 IP 图生图（sync/async），并进行统一梳理后的落地与验证。

## Goals

- 虚拟 IP 图生图链路（sync + variants-async + Celery worker）统一使用 `normalize_image_gen_request` + `build_ai_manager_call`。
- 将 endpoint 变薄，减少重复的 provider/model/refs/size/aspect_ratio 处理代码。
- 补齐/调整测试覆盖与真实浏览器 E2E 验证记录。

## Changes

- 新增 `ai-pic-backend/app/services/virtual_ip/image_variant_service.py`：
  - `resolve_virtual_ip_variant_request(...)`：统一从 payload/form 合并字段（prompt/model/count/size/aspect_ratio/style/style_spec/reference_images）。
  - `generate_virtual_ip_image_variants(...)`：基于归一化层构建安全参数并调用 `ai_manager.image_to_image`，统一持久化与 VirtualIPImage 写入元数据。
- 新增 `ai-pic-backend/app/services/image_gen/coerce.py`：抽出 payload 值处理通用函数（clean_str/maybe_int/coerce_str_list/value_from_payload）。
- 更新 `ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/variants.py`：
  - sync `/variants` 与 async `/variants-async` 统一走 service；async 仅创建 Task 并投递 Celery。
- 拆分 worker：新增 `ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_variant_task.py`，并在 `ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/__init__.py` 中导出。
  - `ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py` 保留文生图 worker，移除图生图 worker，降低文件体积与职责耦合。
- 更新测试 `ai-pic-backend/tests/test_api.py`：
  - 移除已不再需要的文件系统 monkeypatch。
  - 追加断言：`google:...` 前缀模型被归一化为 `prefer_provider=google` 且 `model=gemini-3-pro-image-preview`（确保 Phase 2 的核心行为可回归）。

## Validation

- Backend quick gate：
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
  - `cd ai-pic-backend && pytest tests/test_api.py::TestVirtualIPAPI::test_generate_virtual_ip_image_variant -q`
- Chrome E2E（Docker dev + Nginx，`http://localhost:8089`）：
  1. 重启容器以加载 Celery 代码变更：`docker compose -f docker/docker-compose.dev.yml restart ai-video-backend ai-video-celery-worker`
  2. 登录：`http://localhost:8089/login`（`geyunfei` / `Gyf@845261`）
  3. 打开虚拟 IP 详情页并进入图片管理区：`http://localhost:8089/virtual-ip/1`
  4. 在某张图片卡片点击「图生图」，直接点击「提交图生图任务」
  5. 观察网络请求：`POST /api/v1/virtual-ips/1/images/1/variants-async` 返回 `{task_id: 539, status: "pending"}`
  6. 跳转任务管理：`http://localhost:8089/tasks`，任务最终显示失败（上游图生图 provider 不可用，错误为“所有图生图提供商都失败了”）；确认链路已跑通且无导入/运行时异常。

## Next Steps

- Phase 3：接入环境文生图/图生图（保持环境域禁用 style_spec 的 policy），并补充同等粒度的单测 + Chrome E2E 记录。
- 评估“model 前缀 provider 未启用”场景的降级策略（是否允许 fallback 或在 UI 层阻断）。

## Linked Commits

- TBD
