---
id: 2025-12-18T12-54-54Z-env-image-download-retry
date: 2025-12-18T12:54:54Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment, build]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - .dockerignore
summary: "Add retries and clearer errors for environment image downloads; add .dockerignore to fix docker build context."
---

## User Prompt

- 环境文生图任务报“图像下载失败”，需要排查并继续完成验证。

## Goals

- 提高环境图下载/持久化的稳健性，暴露具体错误原因。
- 让 docker 生产镜像构建避免将 node_modules 等发到上下文导致失败。
- 重新跑必需的验证（pre-commit quick gate、build_prod_images）。

## Changes

- `ai_service._download_image`：改为抛出详细异常、增加 3 次重试和等待，并记录失败日志，保证上层能看到具体报错。
- `ai_service._persist_generated_image` 直接复用抛错路径，不再吞掉下载异常。
- 新增根目录 `.dockerignore`，排除 `node_modules`、上传目录、缓存等，修复 `docker/build_prod_images.sh` 因长路径/链接报错。

## Validation

- `pre-commit run --files ai-pic-backend/app/services/ai_service.py`（通过）。
- `bash docker/build_prod_images.sh`（通过，镜像 tag 0c69a9c）。
- 未重跑全量 `pytest`（基线已有大量 fixture/DB 相关失败），依赖 pre-commit backend quick gate。

## Next Steps

- 部署后重试环境文生图任务；若仍失败，查看日志中新的具体错误，确认是否为 URL 过期/网络问题。
- 如需追加 MiniMax 图生图模型，提供官方模型 ID 与能力列表后补充到 provider。

## Linked Commits

- (pending)
