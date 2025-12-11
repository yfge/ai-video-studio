#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REGISTRY="registry.cn-beijing.aliyuncs.com/geyunfei"
GIT_SHA="$(git rev-parse --short HEAD)"
IMAGE_TAG="${GIT_SHA}"

BACKEND_IMAGE="${REGISTRY}/ai-video-backend:${IMAGE_TAG}"
FRONTEND_IMAGE="${REGISTRY}/ai-video-frontend:${IMAGE_TAG}"

echo "[build_prod_images] Using tag: ${IMAGE_TAG}"
echo "[build_prod_images] Backend image:  ${BACKEND_IMAGE}"
echo "[build_prod_images] Frontend image: ${FRONTEND_IMAGE}"

echo "[build_prod_images] Ensuring buildx builder is available..."
if ! docker buildx inspect >/dev/null 2>&1; then
  docker buildx create --use --name ai-video-studio-builder
fi

echo "[build_prod_images] Building and pushing backend image..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "${BACKEND_IMAGE}" \
  -f docker/Dockerfile.backend.prod \
  --push \
  .

echo "[build_prod_images] Building and pushing frontend image..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "${FRONTEND_IMAGE}" \
  -f docker/Dockerfile.frontend.prod \
  --push \
  .

echo "[build_prod_images] Done."
echo "[build_prod_images] To run with docker-compose.prod.yml, set IMAGE_TAG=${IMAGE_TAG}"

