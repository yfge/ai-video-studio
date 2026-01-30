---
id: 2026-01-14T10-35-30Z-docker-base-image-mirror
date: 2026-01-14T10:35:30Z
participants: [human, codex]
models: [gpt-5.2]
tags: [docker, build]
related_paths:
  - docker/Dockerfile.backend.prod
  - docker/Dockerfile.frontend.prod
summary: "Switch prod Docker base images to dockerproxy to avoid Docker Hub timeouts"
---

## User Prompt

全局检查文生图/图生图提示词规范，并在选择不同 provider 时动态加载输入；要求原子化提交并在每次提交前执行 `./docker/build_prod_images.sh`。

## Goals

- 保障 `./docker/build_prod_images.sh` 在当前网络环境下可稳定构建/推送生产镜像
- 为后续前端 provider-aware UI 改动提供可用的提交/验证通路

## Changes

- 更新生产 Dockerfile 的基础镜像来源为 `dockerproxy.com`：
  - `docker/Dockerfile.backend.prod`：`python:3.11-slim` → `dockerproxy.com/library/python:3.11-slim`
  - `docker/Dockerfile.frontend.prod`：`node:20-alpine` → `dockerproxy.com/library/node:20-alpine`

## Validation

- `./docker/build_prod_images.sh`（成功；修复 Docker Hub `TLS handshake timeout` 导致的构建失败）

## Next Steps

- 继续推进前端 provider-aware 的文生图/图生图高级参数 UI，并补齐 Chrome E2E 验证与分布提交

## Linked Commits

- (pending)
