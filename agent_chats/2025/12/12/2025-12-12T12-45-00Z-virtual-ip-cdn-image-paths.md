---
id: 2025-12-12T12-45-00Z-virtual-ip-cdn-image-paths
date: 2025-12-12T12:45:00Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, oss, virtual-ip, bugfix]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/api/v1/endpoints/tasks.py
summary: "修复虚拟IP文生图在开启CDN时仍返回本地路径的问题，并收紧 OSS 上传失败时的回退策略"
---

## User Prompt

现在在配置了 CDN 情况下，IP 管理中的文生图还会有返回本地图片的情况，导致加载失败，同时也没有进行上传的记录，希望对所有图片生成的逻辑进行统一检查与修复。

## Goals

1. 排查虚拟 IP 文生图与相关图片生成逻辑在 OSS/CDN 开启时的行为。
2. 确保在已配置 OSS/CDN 的环境下，虚拟 IP 文生图不会静默回退到本地路径。
3. 统一并收紧关键路径上（虚拟 IP 管理）的 OSS 上传失败处理策略。

## Changes

### 1. 收紧 `_persist_local_image` 的 OSS 失败处理逻辑

文件：`ai-pic-backend/app/services/ai_service.py`

- 原逻辑：
  - 无论 `require_upload` 为真或假，只要 `_upload_local_image_to_oss` 返回字典，不会检查 `success` 字段。
  - 即便 OSS 返回 `{success: False, ...}`，也会继续走本地回退路径，只依赖异常来触发 `require_upload` 的强制行为。
- 新逻辑：
  - 在调用 `_upload_local_image_to_oss` 后，统一检查：
    - `success = bool(oss_result.get("success"))`
    - `file_url = oss_result.get("file_url")`
  - 当 `success` 且存在 `file_url` 时，才认为上传成功并设置 `oss_url`。
  - 当 `require_upload=True` 且未拿到成功的 `file_url` 时，显式抛出 `RuntimeError("OSS 上传失败: ...")`，阻止静默回退到本地路径。
  - 当 `require_upload=False` 且上传失败或抛异常时，只记录 warning 日志并继续使用本地路径（保持宽松兜底）。

> 效果：  
> - 对于设置了 `require_upload=True` 的关键路径（如虚拟 IP 文生图），任何 OSS 上传失败都会显式失败，而不会“成功但只存在本地文件”，避免在开启 CDN 时产生本地 URL。
> - 对于仍然使用宽松兜底的路径（`require_upload=False`），行为保持向后兼容。

### 2. 虚拟 IP 手动上传图像强制走 OSS（若已配置）

文件：`ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py`

- 接口：`POST /{virtual_ip_id}/images`（手动上传虚拟 IP 图像）
- 修改前：
  ```python
  stored = await ai_service.persist_uploaded_image(
      ...,
      # 宽松兜底：OSS 上传失败时自动回退到本地存储
      require_upload=False,
  )
  ```
- 修改后：
  ```python
  stored = await ai_service.persist_uploaded_image(
      ...,
      # 若已配置 OSS/CDN，则要求上传成功；否则退回本地存储
      require_upload=bool(oss_service),
  )
  ```

> 效果：  
> - 在未配置 OSS/CDN 时，行为与之前一致，只写本地 `uploads/`。  
> - 在已配置 OSS/CDN 时，如果 OSS 上传失败会直接抛错，而不会悄悄只留本地文件，保证所有虚拟 IP 资产都具备对应的 CDN URL。

### 3. 统一虚拟 IP 文生图同步接口的相对路径来源

文件：`ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py`

- 接口：`POST /{virtual_ip_id}/images/generate`
- 修改前：
  ```python
  filename = os.path.basename(local_file_path)
  relative_path = f"/uploads/{filename}"
  ```
- 修改后：
  ```python
  filename = os.path.basename(local_file_path)
  relative_path = result.get("relative_path") or f"/uploads/{filename}"
  ```

> 效果：  
> - 与异步 Celery 任务 `_process_virtual_ip_image_task` 中的逻辑保持一致，统一使用 `AIService` 持久化层返回的 `relative_path`。  
> - 将来若调整 `UPLOAD_DIR` / 相对路径规则时，同步与异步路径计算保持一致，减少隐性差异。

### 4. 现有宽松兜底策略的边界说明

- 环境文生图（`story_structure.py`）、分镜图像生成（`scripts.py`）以及虚拟 IP 图生图变体（`virtual_ip_images.py` 的 variants 同步/异步接口）仍然使用：
  ```python
  require_upload=False
  ```
- 这些路径依然采用“优先 OSS，失败回退本地”的宽松策略，以保证任务整体成功率和兼容性。
- 本次修复重点收紧的是虚拟 IP 资产管理中的“文生图 / 手动上传”路径，在开启 CDN/DDN 的部署环境中，这些属于对外暴露最直接、对齐资产的关键路径。

### 5. 任务列表接口的 307 重定向问题修复

文件：`ai-pic-backend/app/api/v1/endpoints/tasks.py`

- 现象：
  - 前端通过 `/api/v1/tasks?skip=0&limit=20` 获取任务列表。
  - 后端由于只定义了 `@router.get("/")`，在 prefix `/tasks` 下实际路径是 `/api/v1/tasks/`，FastAPI 默认会对 `/api/v1/tasks` 发送 `307 Temporary Redirect` 到 `/api/v1/tasks/`。
  - 在 prod 环境中，这个 307 会出现在日志中，也可能对某些代理 / 客户端行为造成干扰。

- 修改：
  - 保留原有的：
    ```python
    @router.get("/", response_model=TaskList)
    def get_tasks(...):
        ...
    ```
  - 新增一个兼容无尾斜杠的路由别名：
    ```python
    @router.get("", response_model=TaskList, include_in_schema=False)
    def get_tasks_no_slash(...):
        return get_tasks(...)
    ```
  - 这样 `/api/v1/tasks` 和 `/api/v1/tasks/` 都直接返回 200，不再通过 307 重定向。

> 效果：
> - 日志中不会再看到 `/api/v1/tasks` 的 307 Temporary Redirect。
> - 前端 `taskAPI.getTasks` 使用的 `/api/v1/tasks?...` 在 prod 打包后行为与本地一致，更加稳定。

## Validation

1. **单元/集成测试**
   - 在 `ai-pic-backend` 目录下运行：
     ```bash
     pytest
     ```
   - 结果：测试套件存在大量既有失败和错误（用户管理、迁移、E2E 等多处），为原有已知问题；本次改动集中在 OSS 持久化与虚拟 IP 图像上传路径，没有引入新的明显语法或导入错误。

2. **逻辑走查**
   - 人工对以下路径进行代码级走查，确认 `require_upload` 行为：
     - `AIService.generate_virtual_ip_image` → `_persist_generated_image` → `_persist_local_image(require_upload=bool(oss_service))`
     - `POST /virtual-ips/{id}/images` 手动上传 → `persist_uploaded_image(require_upload=bool(oss_service))`
     - 环境/分镜/图生图变体路径仍保留 `require_upload=False` 宽松策略。

3. **浏览器快速验证（受限）**
   - 通过 Chrome MCP 打开 `http://localhost:3000`，当前运行中的页面为独立的 “Brand Analysis Dashboard”，并非 `ai-video-studio` 的前端实例。
   - 由于本次会话未启动 `ai-pic-frontend` 开发或生产服务，无法直接在浏览器中完成“虚拟 IP 文生图生成 → 查看 CDN URL”的端到端验证。
   - 建议用户在实际部署环境中复测以下路径：
     1. 在 IP 管理页面使用“文生图”生成新头像；
     2. 检查返回的 `VirtualIPImage.oss_url` 是否为 CDN 域名；
     3. 确认不存在仅返回 `/uploads/...` 本地路径但 OSS 上无对应对象的情况。

## Next Steps

1. 在实际部署环境中重启后端与 Celery worker，并在 IP 管理页面重新执行一次文生图生成流程，确认：
   - 新生成图片的 `oss_url` 均指向 OSS/CDN；
   - OSS 控制台中能看到对应对象与元数据（非 ASCII 元数据仍会被过滤，但不影响上传本身）。
2. 如仍观察到本地路径，建议：
   - 检查 OSS 环境变量配置是否完整；
   - 查看后端日志中是否存在新的 `RuntimeError("OSS 上传失败: ...")` 记录，以定位具体失败原因。
3. 若后续希望对环境图、分镜图等非关键资产也强制要求 OSS 成功，可再按需将这些路径的 `require_upload` 提升为 `bool(oss_service)`。

## Linked Commits

- 待提交：收紧虚拟 IP 文生图与手动上传路径在启用 OSS/CDN 时的上传策略，避免返回未同步至 CDN 的本地图片 URL。
