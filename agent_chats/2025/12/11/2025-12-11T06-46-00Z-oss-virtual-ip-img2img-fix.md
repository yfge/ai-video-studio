---
id: 2025-12-11T06-46-00Z-oss-virtual-ip-img2img-fix
date: 2025-12-11T06:46:00Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, oss, virtual-ip]
related_paths:
  - AGENTS.md
  - ai-pic-backend/app/services/storage/oss_service.py
  - ai-pic-backend/app/services/diagnostic_service.py
  - ai-pic-backend/app/api/v1/endpoints/diagnostic.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip.py
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/app/models/virtual_ip.py
  - ai-pic-backend/app/models/story_structure.py
  - ai-pic-backend/app/models/script.py
  - ai-pic-backend/app/models/user.py
  - ai-pic-backend/alembic/versions/f3c2d1e4a5b6_add_user_id_to_core_assets.py
  - ai-pic-frontend/src/app/page.tsx
summary: "Fix OSS upload for virtual IP image variants, add per-user asset ownership, and update agents guidance to forbid '嘴硬'."
---

## User Prompt

- 多轮对话中，用户要求：修复虚拟 IP / 环境 / 分镜图像在配置 OSS 时的上传问题（403 SignatureDoesNotMatch），确保所有生成图片走 OSS；梳理模型解析和图生图逻辑；并强调“不能嘴硬”，需要在 AGENTS.md 中写清楚这一点。

## Goals

- 统一并修复 OSS 上传抽象，避免再出现手写签名导致的 403。
- 确保虚拟 IP 文生图 / 图生图、环境图、分镜图都通过同一 OSS 抽象，配置 OSS 时上传必须成功。
- 为虚拟 IP、故事、环境等核心资产增加 user_id 归属，只让当前用户看到自己的资产（管理员例外）。
- 在 AGENTS.md 中新增“不要嘴硬”的强制行为规范。

## Changes

- `app/services/storage/oss_service.py`：
  - 改为统一通过 `oss2.Bucket.put_object` 上传，由官方 SDK 负责签名，删除旧的 `httpx + hmac` 手写签名路径。
  - 读取 `ALIYUN_*` 配置时统一 `strip()` 去掉空白，规范化 endpoint host。
  - 调整上传逻辑：不再显式设置 `Content-Type` 头，由 SDK 处理；元数据只接受 ASCII。
  - 对 metadata key 做归一化：将下划线替换为短横线，构造形如 `x-oss-meta-virtual-ip-id`，避免客户端/服务端 canonicalization 差异导致 SignatureDoesNotMatch。
- `app/services/ai_service.py`：
  - `_upload_local_image_to_oss` 和 `_persist_generated_image` 始终通过 `oss_service.upload_file_content` 走统一抽象。
  - 保持 `require_upload=bool(oss_service)`，在配置 OSS 时上传失败会直接抛错，不再静默回退到本地 `/uploads`。
- `app/api/v1/endpoints/virtual_ip_images.py`：
  - 虚拟 IP 图生图变体下载后，通过 `_upload_local_image_to_oss` 上传 OSS，存储 `oss_url`，失败时返回 500 并带详细错误。
- `app/services/diagnostic_service.py` / `app/api/v1/endpoints/diagnostic.py`：
  - 增加 `test_oss_image_upload` 以及对应的 `POST /api/v1/diagnostic/oss-image` 接口，使用 1x1 PNG 通过 `upload_file_content` 走完整 OSS 路径自测，并在日志中记录 file_url。
- 用户资产归属相关（前一轮改动，本次一并提交）：
  - 在 `app/models/virtual_ip.py`、`script.py`、`story_structure.py`、`user.py` 中为 VirtualIP / Story / Environment 增加 `user_id` 外键和关系。
  - Alembic 迁移 `f3c2d1e4a5b6_add_user_id_to_core_assets.py`：为上述表增加 `user_id` 列和索引，并把历史数据回填给第一个用户。
  - `app/api/v1/endpoints/virtual_ip.py`、`stories.py`、`episodes.py`、`scripts.py`、`story_structure.py` 中，对列表和详情接口按 `current_user` 过滤，仅管理员可见全局。
- `AGENTS.md`：
  - 在 Delivery Checklist 下新增“CRITICAL — 不要嘴硬”一条，要求 agent 在日志/结果与推断不一致时必须先承认不确定并用真实请求复现问题，不得口头坚持“代码没问题”，并在 `agent_chats` Validation 中记录验证过程。
- `ai-pic-frontend/src/app/page.tsx`：
  - 页脚增加备案号 `京ICP备2024077334号-1`。

## Validation

- 在本地容器环境中：
  - 运行 `python -m py_compile` 对修改过的后端文件进行语法检查（`oss_service.py`、`diagnostic_service.py`、相关 endpoints）。
  - 使用集成脚本 `tests/integration/test_oss_detailed.py` 重现旧实现的 SignatureDoesNotMatch，并验证新 `OSSService.upload_file_content` 可成功上传 PNG 到 `http://resource.lets-gpt.com/...`。
  - 直接在容器内调用 `diagnostic_service.test_oss_image_upload()`，验证 `POST /api/v1/diagnostic/oss-image` 路径下图片上传 + 清理成功。
  - 使用提供的 curl 调用虚拟 IP 图生图变体接口，确认当前错误已从 OSS 403 变为「所有图生图提供商都失败了」，即问题已从存储层移至上游 provider。
- 未在本环境中完整运行 `pytest` / MySQL 集成测试（缺少数据库服务），需要在真实部署环境中补充。

## Next Steps

- 在生产环境中：
  - 针对 OpenAI / Google / Volcengine 等图生图模型做一次端到端自测，确认上游 provider 配置正确，避免 `所有图生图提供商都失败了`。
  - 根据需要为 backend/frontend 添加专用的 `Dockerfile.*.prod` 和 `docker-compose.prod.yml`，用于无挂载的生产部署。
  - 将新 OSS 行为（强制上传、失败即报错）记录到 `OSS_INTEGRATION.md` 和前端使用文档中。

## Linked Commits

- pending

