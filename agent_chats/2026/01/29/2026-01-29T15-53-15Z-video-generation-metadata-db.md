---
id: 2026-01-29T15-53-15Z-video-generation-metadata-db
date: 2026-01-29T15:53:15Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, metadata]
related_paths:
  - ai-pic-backend/alembic/versions/b4d2c8f1a7e9_add_generation_metadata_to_video_tasks.py
  - ai-pic-backend/app/models/video_generation_task.py
  - ai-pic-backend/app/services/video/video_task_generation_metadata.py
  - ai-pic-backend/app/services/video/video_task_polling_service.py
  - ai-pic-backend/app/services/video/video_task_submission_service.py
  - ai-pic-backend/tests/unit/models/test_video_generation_task_model.py
  - ai-pic-backend/tests/unit/services/video/test_video_task_generation_metadata.py
  - docs/media-asset-persistence.md
  - tasks.md
summary: "Persist normalized video generation metadata in DB for consistent consumption across providers."
---

## User Prompt

继续按 `tasks.md` 推进（选 1），把生成链路的元数据统一落库，减少 provider 分叉与重复字段。

## Goals

- 为分镜视频任务提供统一的落库 generation metadata（provider/model/task_id/width/height/duration/mime/sha256/OSS refs）。
- 保持改动原子化：包含迁移、代码、测试、文档与 task board 更新。

## Changes

- 新增 `video_generation_tasks.generation_metadata`（JSON）用于存储规范化元数据。
- 新增 `build_video_generation_metadata()`，从提交参数 + OSS 上传结果抽取统一字段（含 720p + ratio 的宽高推断）。
- 在视频任务提交与轮询成功落库时写入 `generation_metadata`。
- 新增单元测试覆盖：模型列存在性 + 元数据构建逻辑。
- 更新 `docs/media-asset-persistence.md` 与 `tasks.md` 对应条目。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`

## Next Steps

- 将同样的 generation metadata 结构扩展到图片/音频落库路径（VirtualIP/Environment/Storyboard 产物）。
- 完成 P0-3：角色集中管理 + readiness 检查 + 生成后一致性校验 + deepseek/banana/veo3 全流程 E2E。

## Linked Commits

- （待提交）
