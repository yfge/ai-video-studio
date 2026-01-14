---
id: 2026-01-14T11-47-09Z-docker-base-images-configurable
date: 2026-01-14T11:47:09Z
participants: [human, codex]
models: [gpt-5.2]
tags: [docker, chore]
related_paths:
  - docker/Dockerfile.backend.prod
  - docker/Dockerfile.frontend.prod
summary: "Make Docker base images configurable to reduce build flakiness"
---

## User Prompt

继续推进 provider-aware 文生图/图生图优化，并保持原子化提交与生产镜像可构建。

## Goals

- 降低 `./docker/build_prod_images.sh` 因镜像源波动导致的构建失败风险
- 保留在不同环境（Docker Hub / 代理镜像）切换 base image 的能力

## Changes

- 让 `docker/Dockerfile.backend.prod` 支持通过 `PYTHON_BASE_IMAGE` 覆盖基础镜像（默认 `python:3.11-slim`）
- 让 `docker/Dockerfile.frontend.prod` 支持通过 `NODE_BASE_IMAGE` 覆盖基础镜像（默认 `node:20-alpine`）

## Validation

- `./docker/build_prod_images.sh`

## Next Steps

- 恢复并提交 img2img modal refactor（stash）
- 基于 `metadata.ui.image_gen` 在前端动态显示/隐藏高级参数输入

## Linked Commits

- N/A (pending)
