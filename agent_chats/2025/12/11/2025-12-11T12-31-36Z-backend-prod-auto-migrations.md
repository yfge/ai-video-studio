---
id: 2025-12-11T12-31-36Z-backend-prod-auto-migrations
date: 2025-12-11T12:31:36Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, docker, migrations]
related_paths:
  - docker/backend-entrypoint.sh
  - docker/Dockerfile.backend.prod
  - docker/docker-compose.prod.yml
summary: "Ensure production backend runs Alembic migrations automatically on startup using the same entrypoint as dev, with reload only enabled in dev."
---

## User Prompt

生产环境中后端容器启动时不会自动运行 Alembic 迁移，需要手动进入容器执行 `alembic upgrade head`，希望像开发环境一样自动应用数据库迁移，但在生产使用多 worker、无 reload 的模式。

## Goals

- 复用当前开发用的 `backend-entrypoint.sh` 逻辑，让生产也在启动时自动执行 `alembic upgrade head`。
- 区分 dev/prod：开发环境仍然用 `--reload`，生产环境使用多 worker、无 reload。
- 不改变现有 API 行为，只调整启动流程和 Docker 配置。

## Changes

- 更新 `docker/backend-entrypoint.sh`：
  - 保留原有逻辑：检查 `DATABASE_URL` → 等待数据库就绪 → 执行 `alembic upgrade head`。
  - 将最后的启动命令改为根据环境变量分支：
    - 当 `UVICORN_RELOAD=1`（dev）时，使用 `uvicorn main:app --reload`。
    - 否则（prod），读取 `UVICORN_WORKERS`（默认 4），执行 `uvicorn main:app --workers <N>`。
- 更新 `docker/Dockerfile.backend.prod`：
  - 将 `backend-entrypoint.sh` 拷贝到镜像 `/app/backend-entrypoint.sh` 并赋予可执行权限。
  - 设置环境变量：
    - `UVICORN_WORKERS=4`
    - `UVICORN_RELOAD=0`（生产默认关闭 reload）。
  - 将 `CMD` 修改为 `["/bin/bash", "/app/backend-entrypoint.sh"]`，让生产也走统一的入口脚本。
- 更新 `docker/docker-compose.prod.yml`：
  - 后端服务 `ai-video-backend` 的 `command` 改为显式调用入口脚本：
    ```yaml
    command: ["/bin/bash", "/app/backend-entrypoint.sh"]
    ```
  - 保持 `env_file: .env`，卷映射仍然指向 `/app/ai-pic-backend/uploads`。

## Validation

- 本地通过 `python -m compileall` 对 backend 代码做语法检查；入口脚本本身是 shell，无需编译。
- 使用 `docker/dev_in_docker.sh` 启动开发栈，观察日志：
  - `backend-entrypoint` 成功等待数据库并执行 `alembic upgrade head`。
  - dev 模式下显示 `Using reload mode for development`，并以 `uvicorn --reload` 方式运行。
- 生产路径推演：
  - 通过 `Dockerfile.backend.prod` 构建生产镜像，`UVICORN_RELOAD=0`，`UVICORN_WORKERS=4`。
  - `docker-compose.prod.yml` 启动时，后端容器同样执行等待数据库 → 迁移 → `uvicorn --workers 4`。

## Next Steps

- 在生产机上用最新镜像（包含入口脚本改动）执行：
  - `IMAGE_TAG=<new> docker compose -f docker/docker-compose.prod.yml pull`
  - `IMAGE_TAG=<new> docker compose -f docker/docker-compose.prod.yml up -d`
- 后续如需调整 worker 数，可以仅通过环境变量 `UVICORN_WORKERS` 控制，而无需改 Dockerfile。

## Linked Commits

- （待补充）`fix(backend): run alembic migrations on prod startup` 提交关联此更改。

