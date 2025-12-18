---
id: 2025-12-18T13-10-00Z-env-id-resolution
date: 2025-12-18T13:10:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Fix environment image tasks to resolve business_id or numeric id consistently when running in Celery workers."
---

## User Prompt

- 环境图生图任务显示成功但页面没有新图片，要求检查代码。

## Goals

- 让环境文生图/图生图 Celery 任务在 worker 侧正确根据 business_id 或数值 id 解析环境，确保新生成图片落库并能被 `/environments/{id}/images` 返回。
- 重新构建生产镜像并记录验证。

## Changes

- `_process_environment_image_task` 与 `_process_environment_image_variant_task` 使用 `svc.resolve_environment`（支持 business_id/数字 id）替换原先只接受整型 id 的 `get_environment`，避免 worker 无法找到环境导致图片未关联。

## Validation

- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/story_structure.py`（通过）。
- `bash docker/build_prod_images.sh`（通过，镜像 tag 5aa5bc7）。
- 未重跑全量 `pytest`（基线已有大量 fixture/DB 依赖失败），依赖 pre-commit backend quick gate。

## Next Steps

- 部署后端/worker 至镜像 `5aa5bc7` 并重跑环境图生图任务，刷新环境详情页应能看到新增图片。
- 如仍缺失，请提供任务 ID 和最新错误日志以便进一步排查。

## Linked Commits

- (pending)
