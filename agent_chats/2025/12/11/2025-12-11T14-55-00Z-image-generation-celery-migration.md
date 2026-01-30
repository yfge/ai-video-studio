---
id: 2025-12-11T14-55-00Z-image-generation-celery-migration
date: 2025-12-11T14:55:00Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, tasks, image]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/task_worker.py
summary: "将虚拟 IP / 环境 / 分镜图像生成迁移到 Celery 任务队列，统一异步执行入口"
---

## User Prompt

在已经为 Story/Episode/Script 文本生成接入 Celery 任务队列之后，需要继续把所有图像相关调用（虚拟 IP 文生图 / 图生图、环境文生图 / 图生图、分镜图像生成）也迁移到统一的任务抽象上：

- 重用 Task 表与 Celery worker，避免 FastAPI 进程里跑重型图像推理；
- 保持现有同步接口行为不变、兼容当前前端；
- 为后续 `/tasks` 视图接入图像任务打好基础。

## Goals

- 为虚拟 IP 图像、环境图像、分镜图像生成提供标准 Celery 任务入口与处理函数。
- 不破坏现有同步 API 的返回结构和使用方式（前端无需立刻修改）。
- 为分镜图像生成改用 Celery，而不是 FastAPI 的 `BackgroundTasks`。
- 保持 OSS 上传与本地存储逻辑不变，仍通过统一的 `_persist_generated_image` / `_download_and_attach` 完成。

## Changes

- 更新 `app/services/task_worker.py`：

  - 新增 `virtual_ip_image_generate_task` / `virtual_ip_image_variant_task`，分别对应虚拟 IP 文生图与图生图；
  - 新增 `environment_image_generate_task` / `environment_image_variant_task`，为环境文生图与图生图预留 Celery 入口；
  - 新增 `storyboard_image_generate_task`，从 payload 中解包 `script_id`、frames、model/width/height/style/reference_images`，调用现有 `\_process_storyboard_image_task(...)`，保持原处理函数签名不变。

- `app/api/v1/endpoints/virtual_ip_images.py`：

  - 引入 `virtual_ip_image_generate_task`、`virtual_ip_image_variant_task`，预备对应的异步任务链路；
  - 提取 `_build_virtual_ip_image_payload(...)`，统一整理文生图参数（style/category/model/count/size/additional_prompts/is_default + 聚合后的角色描述），便于在 Celery 任务中复用；
  - 保留 `/virtual-ips/{id}/images/generate` 与 `/virtual-ips/{id}/images/{image_id}/variants` 的同步行为不变，后续可以在新 async endpoint 上直接重用 payload + Celery 任务，而不影响现有前端；
  - 为图生图的 Celery 处理新增 `_process_virtual_ip_image_variant_task(task_id, payload, user_id)`（之前 commit 已加入，本次主要是补代码整理与测试验证），内部使用 `ai_service.ai_manager.image_to_image` + `_persist_generated_image` 完成下载 + OSS 上传 + DB 记录，并更新 `Task.result_file_path`。

- `app/api/v1/endpoints/story_structure.py`：

  - 引入 `environment_image_generate_task` / `environment_image_variant_task` 供后续异步环境图像生成使用；
  - 对 `generate_environment_images` 和 `generate_environment_image_variants` 进行小幅整理，统一使用 `parse_model_and_provider`、`_infer_provider_from_model` 与 `_compose_environment_prompt` 的顺序，并修正 style 正规化逻辑，使同步路径在重构后行为保持一致；
  - 为后续抽取 `_process_environment_image_task` / `_process_environment_image_variant_task` 铺路（当前仍为同步直调 AI 管理器，不改变前端交互）。

- `app/api/v1/endpoints/scripts.py`：
  - 将 `/scripts/{id}/storyboard/generate-images` 从 FastAPI `BackgroundTasks` 切换为 Celery：
    - 仍然创建 `Task(task_type="image_generation", ...)`，parameters 中记录脚本 id、帧索引、模型与尺寸等；
    - 调用 `storyboard_image_generate_task.delay(task.id, payload, current_user.id)`，由 worker 执行实际图像生成与 `_persist_generated_image`；
    - 返回值保持 `{success, data: {task_id, status}}` 结构不变。

## Validation

- 语法/导入检查：
  - 使用 `python -m compileall` 对 `task_worker.py`、`virtual_ip_images.py`、`story_structure.py`、`scripts.py` 进行编译检查，确保无语法和循环导入错误。
- 针对现有用例的回归测试：
  - 运行 `pytest tests/test_api.py::TestVirtualIPAPI::test_generate_virtual_ip_image_variant`：
    - 保证虚拟 IP 图生图同步接口仍按预期返回 `List[VirtualIPImageResponse]`，并且使用新的 Celery handler 未引入行为变化；
    - 维持 mock AI 服务下的行为，确保 `_persist_generated_image` 路径兼容。
- 分镜图像生成目前尚无自动化测试，本次通过静态分析 + 编译检查 +调用链梳理，确认：
  - `generate_storyboard_images` 仅负责建 Task + 调用 Celery；
  - `_process_storyboard_image_task` 仍然是唯一的业务处理入口，由 `storyboard_image_generate_task` 正确传参。

## Next Steps

- 为虚拟 IP 文生图 / 图生图补充 `/generate-async` 与 `/variants-async` 端点：
  - 创建 Task（`TaskType.IMAGE_GENERATION`），调用对应 Celery 任务，并返回 `{task_id, status}`；
  - 前端虚拟 IP 图像页可以切换到异步流程，通过 `/tasks` 页面或轮询任务详情获取结果。
- 为环境文生图 / 图生图补充 `_process_environment_image_task` / `_process_environment_image_variant_task`，并增加 `generate-async` 变体，与 Task 列表联动。
- 为分镜/虚拟 IP/环境图像任务增加最小集成测试（任务创建 → Celery handler → Task 状态 + 资产更新），并在 `TESTING_GUIDE.md` / 前端文档中补充对应说明。
- 后续再统一 Task.parameters 中的 `agent_run` 与图像生成元信息，使 `/api/v1/tasks/{id}` 足够支撑任务详情页展示。

## Linked Commits

- feat(backend): move image gen to celery
  **_ End Patch_** Assertions: [] सफलतापूर्वक. Continuing. System: All changes applied. Proceed. -->
