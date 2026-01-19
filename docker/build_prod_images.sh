#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REGISTRY="registry.cn-beijing.aliyuncs.com/geyunfei"
GIT_SHA="$(git rev-parse --short HEAD)"
IMAGE_TAG="${GIT_SHA}"
BUILD_PLATFORMS="${BUILD_PLATFORMS:-linux/amd64,linux/arm64}"
FALLBACK_PLATFORMS="${FALLBACK_PLATFORMS:-linux/amd64}"

BACKEND_IMAGE="${REGISTRY}/ai-video-backend:${IMAGE_TAG}"
FRONTEND_IMAGE="${REGISTRY}/ai-video-frontend:${IMAGE_TAG}"

PYTHON_BASE_IMAGE_ARG=""
if [[ -n "${PYTHON_BASE_IMAGE:-}" ]]; then
  PYTHON_BASE_IMAGE_ARG="--build-arg PYTHON_BASE_IMAGE=${PYTHON_BASE_IMAGE}"
fi

NODE_BASE_IMAGE_ARG=""
if [[ -n "${NODE_BASE_IMAGE:-}" ]]; then
  NODE_BASE_IMAGE_ARG="--build-arg NODE_BASE_IMAGE=${NODE_BASE_IMAGE}"
fi

echo "[build_prod_images] Using tag: ${IMAGE_TAG}"
echo "[build_prod_images] Backend image:  ${BACKEND_IMAGE}"
echo "[build_prod_images] Frontend image: ${FRONTEND_IMAGE}"
echo "[build_prod_images] Platforms:      ${BUILD_PLATFORMS}"

echo "[build_prod_images] Ensuring buildx builder is available..."
if ! docker buildx inspect >/dev/null 2>&1; then
  docker buildx create --use --name ai-video-studio-builder
fi

echo "[build_prod_images] Building and pushing backend image..."
if ! docker buildx build \
  --platform "${BUILD_PLATFORMS}" \
  -t "${BACKEND_IMAGE}" \
  -f docker/Dockerfile.backend.prod \
  ${PYTHON_BASE_IMAGE_ARG} \
  --push \
  .; then
  echo "[build_prod_images] Backend build failed for ${BUILD_PLATFORMS}; retrying ${FALLBACK_PLATFORMS}..."
  docker buildx build \
    --platform "${FALLBACK_PLATFORMS}" \
    -t "${BACKEND_IMAGE}" \
    -f docker/Dockerfile.backend.prod \
    ${PYTHON_BASE_IMAGE_ARG} \
    --push \
    .
fi

echo "[build_prod_images] Building and pushing frontend image..."
if ! docker buildx build \
  --platform "${BUILD_PLATFORMS}" \
  -t "${FRONTEND_IMAGE}" \
  -f docker/Dockerfile.frontend.prod \
  ${NODE_BASE_IMAGE_ARG} \
  --push \
  .; then
  echo "[build_prod_images] Frontend build failed for ${BUILD_PLATFORMS}; retrying ${FALLBACK_PLATFORMS}..."
  docker buildx build \
    --platform "${FALLBACK_PLATFORMS}" \
    -t "${FRONTEND_IMAGE}" \
    -f docker/Dockerfile.frontend.prod \
    ${NODE_BASE_IMAGE_ARG} \
    --push \
    .
fi

echo "[build_prod_images] Done."
echo "[build_prod_images] To run with docker-compose.prod.yml, set IMAGE_TAG=${IMAGE_TAG}"
