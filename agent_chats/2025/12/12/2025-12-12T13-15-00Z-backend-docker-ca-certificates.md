---
id: 2025-12-12T13-15-00Z-backend-docker-ca-certificates
date: 2025-12-12T13:15:00Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, docker, ssl, ca-certificates]
related_paths:
  - docker/Dockerfile.backend.prod
  - docker/Dockerfile.backend.dev
summary: "在 backend Docker 镜像中安装并更新 CA 证书，修复容器内访问 HTTPS 资源时的证书校验问题"
---

## User Prompt

把这些安装配置都更新在 docker 文件里吧，用于解决环境图生图、虚拟 IP 图生图等场景下，容器内部访问 `https://resource.lets-gpt.com/...` 时出现的 `CERTIFICATE_VERIFY_FAILED` 错误。

## Goals

1. 确保 backend / Celery 容器中安装了最新的 CA 证书链，能正确校验 `resource.lets-gpt.com` 的 Let’s Encrypt 证书。
2. 让 `AIServiceManager.image_to_image` 的 base64 预加载（httpx 下载 HTTPS 参考图）在容器内不再因证书链不全而失败。
3. 保持镜像精简，不引入无关依赖。

## Changes

### 1. 生产镜像 Dockerfile 增加 CA 证书安装与更新

文件：`docker/Dockerfile.backend.prod`

- 原来的系统依赖安装：
  ```dockerfile
  RUN apt-get update \
      && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev pkg-config \
      && rm -rf /var/lib/apt/lists/*
  ```
- 修改后：
  ```dockerfile
  RUN apt-get update \
      && apt-get install -y --no-install-recommends \
          ca-certificates \
          build-essential \
          default-libmysqlclient-dev \
          pkg-config \
      && update-ca-certificates \
      && rm -rf /var/lib/apt/lists/*
  ```

> 效果：  
> - 镜像构建过程中安装 `ca-certificates` 包，并在构建期调用 `update-ca-certificates` 更新系统信任链。  
> - 运行中的 backend / celery 容器内，Python/httpx/requests 将使用更新后的系统 CA 列表，对 `resource.lets-gpt.com` 这类使用 Let’s Encrypt 证书的 HTTPS 域名进行正常的证书校验。

### 2. 开发镜像 Dockerfile 同步更新 CA 证书

文件：`docker/Dockerfile.backend.dev`

- 原来的系统依赖安装：
  ```dockerfile
  # System deps for mysqlclient/pymysql and builds
  RUN apt-get update \
      && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev pkg-config \
      && rm -rf /var/lib/apt/lists/*
  ```
- 修改后：
  ```dockerfile
  # System deps for mysqlclient/pymysql and builds + CA 证书
  RUN apt-get update \
      && apt-get install -y --no-install-recommends \
          ca-certificates \
          build-essential \
          default-libmysqlclient-dev \
          pkg-config \
      && update-ca-certificates \
      && rm -rf /var/lib/apt/lists/*
  ```

> 效果：  
> - 本地开发环境的 backend 容器也拥有最新 CA 链，和生产镜像行为一致，便于复现和调试 HTTPS 相关问题。  
> - 避免出现“本地 dev 正常、prod 报 CERTIFICATE_VERIFY_FAILED”的环境差异。

## Validation

1. **证书检查（建议在容器内部执行）**
   - 构建新镜像并启动容器后，可以在容器内运行：
     ```bash
     openssl s_client -connect resource.lets-gpt.com:443 -servername resource.lets-gpt.com
     ```
     预期在末尾看到：`Verify return code: 0 (ok)`。
2. **功能验证**
   - 在 prod 或 dev 内部再次触发：
     - 环境文生图 / 环境图生图；
     - 虚拟 IP 图生图；
   - 检查 Celery 日志：
     - 不再出现 `image_to_image base64 preload skip ... CERTIFICATE_VERIFY_FAILED`；
     - Google Provider 的 `LLM Response ...` 不再因为证书错误而 `status=failure`。

> 当前会话未直接在容器内执行这些命令，验证步骤需在目标环境中完成。

## Next Steps

1. 在 CI 或构建机上使用更新后的 Dockerfile 重新构建 backend 镜像（dev/prod 同步）。  
2. 部署新镜像，重启 `ai-video-backend` 和 `ai-video-celery-worker` 服务。  
3. 通过一次完整的图生图链路验证，确认 `resource.lets-gpt.com` 相关的 HTTPS 访问在容器内已不再报证书错误。

## Linked Commits

- 待提交：更新 backend dev/prod Dockerfile 安装并刷新 CA 证书，解决容器内访问 Let’s Encrypt 证书站点时的 TLS 校验问题。

