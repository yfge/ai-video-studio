---
id: 2025-12-11T06-55-00Z-docker-buildx-prod-images
date: 2025-12-11T06:55:00Z
participants: [human, codex]
models: [gpt-5.1]
tags: [infra, docker, deployment]
related_paths:
  - docker/build_prod_images.sh
  - docker/docker-compose.prod.yml
summary: "Add a buildx-based script to build and push multi-arch production images and wire docker-compose.prod.yml to use them."
---

## User Prompt

- “增加一个脚本，本地build 前后端镜像，记住要用buildx 支持linux amd64 和mac arm64 然后tag:  registry.cn-beijing.aliyuncs.com/geyunfei/[镜像名称]:git head 进行推送”
- “要的是生产镜像 ，顺便把docker-compose.prod 也改了”

## Goals

- Provide a simple script that builds and pushes production backend and frontend images using `docker buildx` with multi-arch support (linux/amd64 and linux/arm64).
- Tag images as `registry.cn-beijing.aliyuncs.com/geyunfei/{image_name}:<git-head>`.
- Update `docker-compose.prod.yml` to reference these registry images instead of rebuilding from source.

## Changes

- `docker/build_prod_images.sh`:
  - New Bash script that:
    - Computes `GIT_SHA=$(git rev-parse --short HEAD)` as the image tag.
    - Constructs backend image tag `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-backend:${GIT_SHA}` and frontend image tag `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-frontend:${GIT_SHA}`.
    - Ensures a `docker buildx` builder exists (`docker buildx inspect` + `docker buildx create --use` if needed).
    - Runs `docker buildx build --platform linux/amd64,linux/arm64 ... --push` for:
      - Backend (`docker/Dockerfile.backend.prod`).
      - Frontend (`docker/Dockerfile.frontend.prod`).
    - Prints the tag and hints to set `IMAGE_TAG=${GIT_SHA}` when using `docker-compose.prod.yml`.
- `docker/docker-compose.prod.yml`:
  - `ai-video-backend`:
    - Switched from `build:` to `image: "registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-backend:${IMAGE_TAG:-latest}"`.
  - `ai-video-frontend`:
    - Switched from `build:` to `image: "registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-frontend:${IMAGE_TAG:-latest}"`.
  - Other service definitions unchanged.

## Validation

- Static validation:
  - Confirmed `docker-compose.prod.yml` YAML structure is valid via visual inspection.
  - `build_prod_images.sh` is syntactically correct Bash and marked executable (`chmod +x`).
- Runtime validation:
  - Not executed here; in a real environment you should run:
    - `cd docker && ./build_prod_images.sh`
    - `IMAGE_TAG=$(git rev-parse --short HEAD) docker compose -f docker-compose.prod.yml up -d`

## Next Steps

- Optionally extend the script to accept an explicit tag argument (e.g., `./build_prod_images.sh my-tag`) instead of always using `git rev-parse`.
- Document this workflow in `docker/README.md` under a “Production deployment” section.

## Linked Commits

- pending

