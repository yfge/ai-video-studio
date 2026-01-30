---
id: 2025-12-11T11-01-32Z-frontend-relative-api-base
date: 2025-12-11T11:01:32Z
participants: [human, codex]
models: [gpt-5.1]
tags: [frontend, api, deployment]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
summary: "Switched frontend API base URL to relative paths so production uses the same origin proxy instead of hardcoded localhost."
---

## User Prompt

前端打包部署后发现 API 基地址仍然是 `http://localhost:8000`，在生产域名 `https://video.lets-gpt.com/` 下访问时不正确，要求把基地址改成空字符串，默认走同域反向代理。

## Goals

- 去掉前端硬编码的 `http://localhost:8000` API 基地址。
- 让生产环境默认通过相对路径 `/api/...` 访问后端，由 Nginx 反向代理到真实 backend。
- 保持 Next.js 15 构建仍然通过。

## Changes

- 更新 `ai-pic-frontend/src/utils/api.ts`：
  - 将 `API_BASE_URL` 从 `process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"` 改为 `process.env.NEXT_PUBLIC_API_URL || ""`。
  - 保留通过 `NEXT_PUBLIC_API_URL` 显式覆盖的能力（开发/特殊部署时可继续使用完整 URL），默认情况下拼接出来的 URL 形如 `"/api/v1/..."`，交由前端所在域名的反向代理转发。

## Validation

- 在 `ai-pic-frontend` 目录运行：
  - `npm run build`：Next.js 15 构建完成，类型检查和静态导出全部通过。
- 手动确认：
  - `ApiClient` 里使用的 `url = \`\${this.baseURL}\${endpoint}\``，当 `baseURL` 为空字符串、`endpoint`为`"/api/v1/..."`时，会生成相对路径，浏览器请求会落在当前域名的`/api/...`。

## Next Steps

- 确认生产环境 Nginx（或其他网关）把 `/api` 前缀正确反向代理到后端（例如容器 `ai-video-backend:8000`）。
- 如果需要在开发环境继续使用 `localhost:8000`，可以在 `.env.local` 或 Docker dev compose 中显式设置 `NEXT_PUBLIC_API_URL=http://localhost:8000`。

## Linked Commits

- （待补充）`fix(frontend): use relative api base` 提交中包含此改动。
