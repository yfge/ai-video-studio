---
id: 2026-01-27T14-47-14Z-tasktype-granular-image-domains
date: 2026-01-27T14:47:14Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, tasks, tasktype, migration, p0]
related_paths:
  - ai-pic-backend/app/models/task.py
  - ai-pic-backend/alembic/versions/39e7d91e9b93_add_granular_image_task_types.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/variants.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_generation.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_variants.py
  - ai-pic-backend/scripts/backfill_task_types.py
  - ai-pic-frontend/src/components/features/tasks/taskTypeOptions.ts
  - ai-pic-frontend/src/utils/api/types/task.types.ts
  - ai-pic-frontend/src/utils/api.ts
  - tasks.md
summary: "Split generic image_generation tasks into domain-specific TaskTypes (storyboard/virtual_ip/environment) with migrations and /tasks filter support."
---

## User Prompt

- 进一步细分 TaskType（例如 storyboard_images / virtual_ip / environment 单独类型）并同步前端过滤选项

## Goals

- 让 `/tasks` 的 `task_type` 过滤能按业务域直接筛选（分镜图像/虚拟IP/环境），避免所有都混在 `image_generation`
- 保持兼容：不改 Task 表结构，只扩展 enum + 更新创建 Task 的入口
- 为后续生产回填提供匹配规则（title/prompt）

## Changes

- Backend: 扩展 `TaskType` 增加：
  - `storyboard_image_generation`
  - `virtual_ip_image_generation`
  - `virtual_ip_image_variant_generation`
  - `environment_image_generation`
  - `environment_image_variant_generation`
- Backend: 更新 Task 创建入口使用新类型：
  - `scripts_legacy.py` 分镜图像生成 → `STORYBOARD_IMAGE_GENERATION`
  - `virtual_ip_images/*` 文生图/图生图 → `VIRTUAL_IP_*`
  - `story_structure/environment_*` 文生图/图生图 → `ENVIRONMENT_*`
- Backend: 更新 `ai-pic-backend/scripts/backfill_task_types.py`，补充上述新类型的识别规则
- Frontend: `/tasks` 类型下拉增加新选项（分镜图像/虚拟IP文生图/虚拟IP图生图/环境文生图/环境图生图）
- Frontend: Task status type 同步支持 `cancelled`（配合上一个 commit 引入的后端 CANCELLED 状态）
- Board: `tasks.md` 补充并勾选“细分 image TaskType”完成项

## Validation

- Backend tests: `cd ai-pic-backend && pytest -q tests/unit/services/test_task_agent_run_persistence_failed.py tests/unit/services/test_task_agent_run_persistence_extra.py`
- Frontend lint: `cd ai-pic-frontend && npm run lint`（0 errors；warnings 见输出）
- Migration (docker): `docker exec ai-video-backend bash -lc 'cd /app/ai-pic-backend && alembic upgrade head'`
- Prod images: `./docker/build_prod_images.sh`（tag=b688d37）
- Chrome E2E (MCP):
  - 登录 `http://localhost:8089/tasks`，确认类型过滤下拉出现新项（分镜图像生成/虚拟IP文生图/虚拟IP图生图/环境文生图/环境图生图）
  - 触发分镜图像任务：`POST /api/v1/scripts/110/storyboard/generate-images` → `task_id=5848`
  - 校验 `GET /api/v1/tasks/5848` 返回 `task_type=storyboard_image_generation`
  - 在 `/tasks` 选择“分镜图像生成”过滤后，仅显示该类型任务

## Next Steps

- 生产分批回填历史任务：先 `--dry-run` 验证匹配率，再按 user/时间范围 `--apply`
- 如需要更细：再拆 `storyboard_image_generation` 为 keyframe/start_end 或按 provider/model 维度做二级标签（不进 enum）

## Linked Commits

- (this commit)

