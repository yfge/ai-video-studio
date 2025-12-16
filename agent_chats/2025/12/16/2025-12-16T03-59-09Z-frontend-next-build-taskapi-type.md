---
id: 2025-12-16T03-59-09Z-frontend-next-build-taskapi-type
date: 2025-12-16T03:59:09Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, build, typescript]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - tasks.md
summary: "Fix Next.js build typecheck errors for task polling and virtual IP voice_config updates."
---

## User Prompt

`next build` 失败：

- Episode 页：`taskAPI.getTask(taskId)` 传了 number，但类型期望 string。
- Virtual IP 页：更新请求包含 `voice_config`，但 `UpdateVirtualIPRequest` 类型缺字段导致编译失败。

## Goals

- 修复 TypeScript 类型错误，确保 `npm run build` 通过。

## Changes

- `ai-pic-frontend/src/app/episodes/[id]/page.tsx`：任务轮询调用改为 `taskAPI.getTask(String(taskId))`。
- `ai-pic-frontend/src/utils/api.ts`：`UpdateVirtualIPRequest` 增加 `voice_config?: VoiceConfig`，与页面提交字段对齐。
- `tasks.md`：补充并勾选该修复项。

## Validation

- `cd ai-pic-frontend && npm run build`

## Next Steps

- 视需要将 `taskAPI.getTask` 的入参类型统一为 `string | number`（内部转换），避免同类问题重复出现。

## Linked Commits

- pending
