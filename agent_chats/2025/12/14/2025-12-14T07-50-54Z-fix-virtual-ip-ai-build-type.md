---
id: 2025-12-14T07-50-54Z-fix-virtual-ip-ai-build-type
date: "2025-12-14T07:50:54Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, virtual-ip, build, typescript]
related_paths:
  - ai-pic-frontend/src/app/virtual-ip/page.tsx
summary: "Fix Next.js build type error in Virtual IP one-click AI flow by avoiding closure capture of optional resp.data."
---

## User Prompt
Docker `next build` 报错：`resp.data is possibly 'undefined'`（Virtual IP 一键生成处）。

## Goals
- 修复 TypeScript 严格类型检查下的构建失败，保持一键生成逻辑不变。

## Changes
- 在 `setNewIP(prev => ...)` 的闭包外先缓存 `const data = resp.data`，避免 TS 在闭包内丢失对 `resp.data` 的非空收窄。

## Validation
- `cd ai-pic-frontend && npm run build`

## Next Steps
- 如 CI 仍提示多 lockfile，建议在镜像构建阶段统一 lockfile 来源（非本次修复范围）。

## Linked Commits
- (pending)

