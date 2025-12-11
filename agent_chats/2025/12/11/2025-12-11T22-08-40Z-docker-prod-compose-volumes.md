---
id: 2025-12-11T22-08-40Z-docker-prod-compose-volumes
date: 2025-12-11T22:08:40Z
participants: [human, codex]
models: [gpt-5.1]
tags: [infra, docker, backend]
related_paths:
  - docker/docker-compose.prod.yml
summary: "Align prod docker-compose Celery uploads volume with backend"
---

## User Prompt

检查 docker-compose.prod 是否和当前行为一致，保证在生产部署下图生图等功能和本地开发环境一致可用，并在提交更改后确保构建配置没有问题。

## Goals

- 核对 `docker/docker-compose.prod.yml` 与 dev 配置，确认 AI 后端与 Celery worker 的运行前提与代码假设一致。
- 确保 Celery worker 在生产环境下也能正确读写 `uploads/` 目录，避免本地与生产行为不一致导致的图片 404 或持久化异常。
- 验证修改后的 compose 文件在语法和 docker compose 解析层面没有问题。

## Changes

- Updated `docker/docker-compose.prod.yml`:
  - 为 `ai-video-celery-worker` 服务增加了与 backend 相同的 `uploads_data` 卷挂载：
    - `uploads_data:/app/ai-pic-backend/uploads`
  - 目的：
    - 保证 Celery worker 中通过 `AIService._persist_generated_image` 或 `persist_uploaded_image` 写入的本地 `uploads` 文件与 backend 容器共享同一物理卷。
    - 与 dev compose 中 backend/worker 共享 `../ai-pic-backend/uploads` 的行为保持一致，避免在生产环境下因为 OSS 上传失败或 fallback 至本地时，实际文件只存在于 worker 容器而导致 backend 静态资源 404。

## Validation

- Infrastructure validation:
  - 运行 `docker compose -f docker/docker-compose.prod.yml config`：
    - 命令成功返回，确认 YAML 语法与引用的卷定义均有效。
    - Docker 仅给出 `version` 字段已废弃的 warning，不影响实际 compose 配置解析。
  - 结合之前在 dev stack 中的验证：
    - Celery worker 通过 HTTP 访问 `http://ai-video-backend:8000/uploads/...` 读取参考图已经验证可行（依赖我们在代码中对 INTERNAL_BACKEND_URL 的解析）。
    - 此次修改确保 worker 写入的 `uploads` 文件和 backend 的静态服务目录一致，使 dev/prod 对本地文件 fallback 行为保持一致。

## Next Steps

- 在下一次生产部署前，建议：
  - 用新的 `docker-compose.prod.yml` 启动一套预生产环境，跑一遍完整的分镜/虚拟 IP 图生图流程，确认：
    - 当 OSS 配置正常时，依旧优先返回 `oss_url`。
    - 当 OSS 故障或关闭时，`/uploads/...` 本地路径在 Nginx + backend 下可直接访问（验证我们刚添加的共享卷生效）。
- 后续如调整 `INTERNAL_BACKEND_URL` 或增加新的 worker 角色（例如视频生成 worker），也建议复用同一 `uploads_data` 卷，保持媒体文件在容器间一致可见。

## Linked Commits

- `chore(docker): share uploads volume to celery worker`

