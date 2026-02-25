---
id: 2026-02-25T01-40-00Z-extract-storyboard-from-scripts-legacy
date: 2026-02-25T01:40:00Z
participants: [human, claude-opus]
models: [claude-opus-4-6]
tags: [refactor, backend, storyboard]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/legacy_generate.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/frame_utils.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/fallback_utils.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_processor.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_refs.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/task_processors.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/generation.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/tests/unit/test_storyboard_image_task_image_gen_persistence.py
summary: "Extract storyboard routes, task processors, and helpers from scripts_legacy.py into storyboard/ package, achieving 51% line reduction"
---

## User Prompt

检查 tasks.md 未完成任务并依次完成。第一个任务：拆分 scripts_legacy.py（4322行）的 storyboard 部分到 storyboard/ 包。

## Goals

- 将 scripts_legacy.py 中所有 storyboard 相关代码（路由、任务处理器、辅助函数）提取到 storyboard/ 端点包
- 达到 scripts_legacy.py 行数减少 ≥40% 的验收指标
- 挂载 storyboard/ 路由器，使新端点生效
- 保持所有测试通过

## Changes

### 新增文件（6个）

1. **storyboard/legacy_generate.py** (299 lines): 从 scripts_legacy.py 迁移的 legacy 分镜生成业务逻辑（去除路由装饰器，转为纯 async 服务函数）
2. **storyboard/frame_utils.py** (230 lines): 分镜帧处理工具（_serialize_frame, _load_existing_frames, _augment_frames, _merge_frames, _normalize_reference_images）
3. **storyboard/fallback_utils.py** (169 lines): 分镜 fallback 生成工具（_compose_fallback_text, _trim_local, _collect_dialogues_for_scene, _collect_stage_for_scene）
4. **storyboard/image_task_processor.py** (302 lines): 分镜图像生成任务处理器（从 _process_storyboard_image_task 拆出）
5. **storyboard/image_task_refs.py** (242 lines): 分镜图像参考图构建逻辑（环境、角色、标签参考图加载）
6. **storyboard/task_processors.py** (113 lines): 分镜生成任务 + 视频任务处理器

### 修改文件（5个）

1. **scripts_legacy.py**: 4322 → 2101 行（**-51%**），移除全部 storyboard 路由、任务处理器和专用辅助函数
2. **scripts/__init__.py**: 更新导入路径，从 storyboard/ 包导入任务处理函数；挂载 storyboard_router
3. **storyboard/__init__.py**: 增加 task_processors 和 image_task_processor 的导出
4. **storyboard/generation.py**: 更新 legacy 导入路径（从 legacy_generate.py 而非 scripts_legacy.py）
5. **tests/unit/test_storyboard_image_task_image_gen_persistence.py**: 更新 monkeypatch 路径

## Validation

- `pytest`: 1888 passed, 87 skipped（之前 1831 passed + 1 failed，修复后全部通过）
- `npm run lint`: 0 errors, 6 warnings（均为已有 warning，非本次引入）
- Python import chain 验证: `from app.api.v1.endpoints.scripts import router` → OK
- 所有 re-export 的函数（_process_storyboard_*_task, _augment_frames, _merge_frames 等）均可通过 scripts/__init__.py 正常访问

## Next Steps

- 继续 tasks.md 下一个 Refactor 任务：拆分 dialogue_audio_service.py
- 后续可进一步将 legacy_generate.py 的业务逻辑迁移到 services 层
- generation.py (325 lines) 和 image_task_processor.py (302 lines) 略超 300 行限制，后续可微调

## Linked Commits

- （待提交）
