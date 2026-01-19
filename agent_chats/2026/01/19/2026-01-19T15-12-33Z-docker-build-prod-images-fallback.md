---
id: 2026-01-19T15-12-33Z-docker-build-prod-images-fallback
date: 2026-01-19T15:12:33Z
participants: [human, codex]
models: [gpt-5.2]
tags: [devops, docker]
related_paths:
  - docker/build_prod_images.sh
summary: "Make prod image build more reliable by adding platform fallback and optional base-image overrides."
---

## User Prompt

原子化分布提交；并保证每次提交前 `./docker/build_prod_images.sh` 可构建。

## Goals

- 提升 `build_prod_images.sh` 在多架构构建时的稳定性，避免因上游镜像拉取/构建偶发失败导致无法提交。
- 保持默认行为不变，同时允许通过环境变量覆盖 base image 以便排查镜像源问题。

## Changes

- 更新 `docker/build_prod_images.sh`：
  - 新增 `BUILD_PLATFORMS`（默认 `linux/amd64,linux/arm64`）与 `FALLBACK_PLATFORMS`（默认 `linux/amd64`），多架构失败时自动回退单架构重试。
  - 支持可选环境变量 `PYTHON_BASE_IMAGE` / `NODE_BASE_IMAGE`，通过 `--build-arg` 传入后端/前端 Dockerfile 以覆盖基础镜像。

## Validation

- 运行 `./docker/build_prod_images.sh`，后端与前端生产镜像均成功构建并 push（默认平台配置）。

## Next Steps

- 恢复并提交短剧故事大纲/剧本生成的节奏模板输入字段（DeepSeek 文生文），再继续跑完整短剧 E2E（含逐张下载验图）。

## Linked Commits

- (pending) `chore(docker): add build platform fallback`

