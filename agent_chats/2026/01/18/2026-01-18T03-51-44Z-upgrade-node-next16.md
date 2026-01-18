---
id: 2026-01-18T03-51-44Z-upgrade-node-next16
date: 2026-01-18T03:51:44Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, deps, docker]
related_paths:
  - AGENTS.md
  - README.md
  - README_EN.md
  - tasks.md
  - ai-pic-frontend/PROJECT_SUMMARY.md
  - ai-pic-frontend/README.md
  - ai-pic-frontend/eslint.config.mjs
  - ai-pic-frontend/package-lock.json
  - ai-pic-frontend/package.json
  - ai-pic-frontend/tsconfig.json
  - docker/Dockerfile.frontend.dev
  - docker/Dockerfile.frontend.prod
summary: "Upgraded frontend to Node 22.20.0 + Next.js 16.1.3, updated lint workflow and docs."
---

## User Prompt

参考 `dev/yfge/ai-shifu` 把 node 和 next.js 升级到最新。

## Goals

- 升级前端 Node 版本与生产镜像一致，并对齐 Docker 基础镜像。
- 升级 Next.js 到最新版本并确保 `npm run lint` / `npm run build` 可用。
- 更新任务看板与文档，确保版本信息一致。

## Changes

- 升级 `ai-pic-frontend` 依赖：Next `16.1.3`、React/ReactDOM `19.2.3`，并加入 `engines.node=22.20.0`。
- 适配 Next 16：`npm run lint` 从 `next lint` 改为 `eslint .`，并调整 `ai-pic-frontend/eslint.config.mjs`（追加项目/测试 overrides）。
- Next 16 构建要求：更新 `ai-pic-frontend/tsconfig.json`（`jsx=react-jsx` + `.next/dev/types` include）。
- Docker：前端 dev/prod 镜像基础镜像升级到 `node:22.20.0-alpine`。
- 文档/看板：同步更新 Next/Node 版本描述，并在 `tasks.md` 记录本次工具链升级完成项。

## Validation

- `cd ai-pic-frontend && npm install`
- `cd ai-pic-frontend && npm run lint`
- `cd ai-pic-frontend && npm run build`
- `./docker/build_prod_images.sh`（成功，IMAGE_TAG=6133758）
- Chrome (MCP) E2E：
  - 访问 `http://localhost:8089/tasks`，点击“退出”
  - 访问 `http://localhost:8089/login`，使用 `geyunfei / Gyf@845261` 登录
  - 访问 `http://localhost:8089/tasks` 与 `http://localhost:8089/virtual-ip` 确认页面正常加载
- 备注：`docker compose -f docker/docker-compose.dev.yml up -d --build` 在 backend 镜像构建阶段因 `langgraph` 包 hash 校验失败而中断（下载内容为空导致 mismatch），因此改为仅重建前端 `ai-video-frontend` 服务用于验证。

## Next Steps

- 评估是否需要把 `eslint` warnings 进一步收敛（例如 `<img>` → `next/image`、未使用变量清理）。
- 排查 `Dockerfile.backend.dev` 的依赖 hash mismatch（若是镜像/网络层面问题，可考虑重试/镜像源策略；若是 requirements hash 过期需更新）。

## Linked Commits

- (pending)

