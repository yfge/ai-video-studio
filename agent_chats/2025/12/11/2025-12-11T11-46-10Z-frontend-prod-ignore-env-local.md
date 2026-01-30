---
id: 2025-12-11T11-46-10Z-frontend-prod-ignore-env-local
date: 2025-12-11T11:46:10Z
participants: [human, codex]
models: [gpt-5.1]
tags: [frontend, docker, env]
related_paths:
  - docker/Dockerfile.frontend.prod
  - ai-pic-frontend/.env.local
summary: "Ensure production frontend images do not bake in local .env.local (with localhost API URL) by removing it in the Docker build stage."
---

## User Prompt

部署后前端依然请求 `http://localhost:8000/api/v1/auth/register`，怀疑是打包时把 `.env` 里的设置带进了生产镜像，而代码已经改成默认相对 `/api`，希望彻底排查并修掉。

## Goals

- 确认为什么生产前端仍然使用 `http://localhost:8000` 作为 API 基地址。
- 确保生产 Docker 镜像构建时不会把本地开发用的 `.env.local`（含 localhost）打进 bundle。
- 保证本地开发仍可利用 `.env.local` 指向本机后端，不影响生产。

## Changes

- 在 `ai-pic-frontend/.env.local` 中发现：
  - `NEXT_PUBLIC_API_URL=http://localhost:8000`，这是本地开发配置，Next.js 会在构建时自动加载。
- 更新 `docker/Dockerfile.frontend.prod` 的 builder 阶段：
  - 之前逻辑：
    ```dockerfile
    COPY ai-pic-frontend ./ai-pic-frontend
    WORKDIR /app/ai-pic-frontend
    ENV NODE_ENV=production
    RUN npm run build
    ```
  - 现在在进入前端工作目录后，显式删除 `.env.local`：
    ```dockerfile
    COPY ai-pic-frontend ./ai-pic-frontend
    WORKDIR /app/ai-pic-frontend
    ## 生产镜像不使用本地开发的 .env.local，避免把 localhost 等开发配置打进 bundle
    RUN rm -f .env.local
    ENV NODE_ENV=production
    RUN npm run build
    ```
  - 这样本地仓库中仍可以保留 `.env.local` 供开发使用，但生产镜像构建时该文件不会存在于容器内，Next.js 构建只会看到 `Dockerfile` 中显式提供的环境（如未来通过 `--build-arg NEXT_PUBLIC_API_URL=` 传入的值）。

## Validation

- 在本地仓库运行 `npm run build`（不经 Docker）以确认前端仍能正常构建，且类型检查与静态导出通过。
- 推断行为：
  - 生产镜像通过 `docker/Dockerfile.frontend.prod` 构建时，在 builder 阶段删除 `.env.local`，因此 `NEXT_PUBLIC_API_URL` 默认为空字符串，`src/utils/api.ts` 将使用相对路径 `/api/...`。
  - 服务通过 `docker-compose.prod.yml` 跑起来后，前端在域名 `https://video.lets-gpt.com` 下访问 `/api/v1/auth/register` 等接口时，将由 Nginx 反向代理到 backend 容器，而不会再发向 `http://localhost:8000`。

## Next Steps

- 在有 Docker 环境的机器上重新执行：
  - `./docker/build_prod_images.sh`
  - 使用脚本输出的最新 `IMAGE_TAG` 更新生产栈：
    `IMAGE_TAG=<tag> docker compose -f docker/docker-compose.prod.yml pull && IMAGE_TAG=<tag> docker compose -f docker/docker-compose.prod.yml up -d`
- 如需为某些环境显式配置 API 地址，可后续在 Dockerfile 中增加 `ARG NEXT_PUBLIC_API_URL` 并在 buildx 命令里通过 `--build-arg` 传入。

## Linked Commits

- （待补充）`fix(frontend): ignore env.local in prod docker build` 提交记录此更改。
