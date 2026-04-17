#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REGISTRY="registry.cn-beijing.aliyuncs.com/geyunfei"
GIT_SHA="$(git rev-parse --short HEAD)"
IMAGE_TAG="${GIT_SHA}"
BUILD_PLATFORMS="${BUILD_PLATFORMS:-linux/amd64,linux/arm64}"
FALLBACK_PLATFORMS="${FALLBACK_PLATFORMS:-linux/amd64}"
BUILD_PUSH="${BUILD_PUSH:-true}"

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
echo "[build_prod_images] Push enabled:   ${BUILD_PUSH}"

use_buildx() {
  [[ "${BUILD_PUSH}" == "true" ]]
}

ensure_buildx() {
  echo "[build_prod_images] Ensuring buildx builder is available..."
  if ! docker buildx inspect >/dev/null 2>&1; then
    docker buildx create --use --name ai-video-studio-builder
  fi
}

build_with_classic() {
  local dockerfile="$1"
  local image="$2"
  local extra_arg="${3:-}"
  local platform="${4:-}"

  echo "[build_prod_images] Classic builder fallback for ${image}"
  if [[ -n "${platform}" ]]; then
    echo "[build_prod_images] Ignoring platform override for classic builder: ${platform}"
  fi
  if [[ -n "${extra_arg}" ]]; then
    DOCKER_BUILDKIT=0 docker build -t "${image}" -f "${dockerfile}" ${extra_arg} .
  else
    DOCKER_BUILDKIT=0 docker build -t "${image}" -f "${dockerfile}" .
  fi
}

build_with_buildx() {
  local image="$1"
  local dockerfile="$2"
  local extra_arg="${3:-}"

  if ! docker buildx build \
    --platform "${BUILD_PLATFORMS}" \
    -t "${image}" \
    -f "${dockerfile}" \
    ${extra_arg} \
    --push \
    .; then
    echo "[build_prod_images] Build failed for ${BUILD_PLATFORMS}; retrying ${FALLBACK_PLATFORMS}..."
    docker buildx build \
      --platform "${FALLBACK_PLATFORMS}" \
      -t "${image}" \
      -f "${dockerfile}" \
      ${extra_arg} \
      --push \
      .
  fi
}

if use_buildx; then
  ensure_buildx
fi

echo "[build_prod_images] Building backend image..."
if use_buildx; then
  build_with_buildx "${BACKEND_IMAGE}" "docker/Dockerfile.backend.prod" "${PYTHON_BASE_IMAGE_ARG}"
else
  build_with_classic "docker/Dockerfile.backend.prod" "${BACKEND_IMAGE}" "${PYTHON_BASE_IMAGE_ARG}" "${BUILD_PLATFORMS}"
fi

echo "[build_prod_images] Building frontend image..."
if use_buildx; then
  build_with_buildx "${FRONTEND_IMAGE}" "docker/Dockerfile.frontend.prod" "${NODE_BASE_IMAGE_ARG}"
else
  build_with_classic "docker/Dockerfile.frontend.prod" "${FRONTEND_IMAGE}" "${NODE_BASE_IMAGE_ARG}" "${BUILD_PLATFORMS}"
fi

echo "[build_prod_images] Done."
if [[ "${BUILD_PUSH}" == "true" ]]; then
  echo "[build_prod_images] To run with docker-compose.prod.yml, set IMAGE_TAG=${IMAGE_TAG}"
else
  echo "[build_prod_images] Images were built locally without push. IMAGE_TAG=${IMAGE_TAG}"
fi
