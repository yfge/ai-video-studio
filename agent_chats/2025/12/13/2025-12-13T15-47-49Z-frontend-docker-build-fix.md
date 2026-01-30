---
id: 2025-12-13T15-47-49Z-frontend-docker-build-fix
date: "2025-12-13T15:47:49Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, docker, build]
related_paths:
  - ai-pic-frontend/src/app/tasks/page.tsx
summary: "Fix Next.js build failure caused by PersistedStyleInfo typing on tasks page."
---

## User Prompt

`docker build` 过程中 `npm run build` 失败：`failed to solve: process \"/bin/sh -c npm run build\" did not complete successfully: exit code: 1`

## Goals

- 修复导致 `next build` 失败的 TypeScript 类型错误
- 确保 `docker/Dockerfile.frontend.prod` 可顺利构建

## Changes

- `ai-pic-frontend/src/app/tasks/page.tsx`
  - 将 `PersistedStyleInfo` 从联合类型调整为单一结构（`style_spec/style_spec_resolution/error` 均为可选），避免在 JSX 多次索引时无法稳定收窄导致的 `style_spec` 属性不存在报错。

## Validation

- Frontend build:
  - `cd ai-pic-frontend && npm run build`
- Frontend lint:
  - `cd ai-pic-frontend && npm run lint`
- Docker build:
  - `docker build -f docker/Dockerfile.frontend.prod . --progress=plain`

## Next Steps

- 如需严格区分成功/失败结构，可用局部变量 + type guard 方式渲染（避免多次 `persistedStyle[task.id]` 访问导致收窄失效）。

## Linked Commits

- fix(frontend): fix tasks page docker build
