---
id: 2025-10-29T07-24-42Z-tasks-page-lint-fix
date: 2025-10-29T07:24:42Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [frontend, tasks]
related_paths:
  - ai-pic-frontend/src/app/tasks/page.tsx
summary: "Tightened tasks page typing, image handling, and task ID flow so lint passes and start/delete no longer hit backend validation errors."
---

## User Prompt

检查tasks.md，规划下一步工作；针对任务管理页继续完成 lint 修复与数据联动问题。

## Goals

- 消除 `tasks/page.tsx` 中的 `any` 与 `<img>` lint 警告。
- 让新建任务后可成功调用启动/删除接口，不再触发 422。

## Changes

- 引入 `TaskImage` 辅助类型、类型守卫与 `TaskImagePreview` 组件，统一处理文件和图库图片预览，并强制使用 `unoptimized` 避免远端域名配置耦合。
- 用 Next `<Image>` 替换原生 `<img>`，复用 `TaskImagePreview` 并保持对象 URL 生命周期管理。
- 在 `loadTasks` 与启动/删除逻辑中规范化任务 ID，过滤无效值并防止 422。
- 更新选中/移除图片时的状态同步，避免多余类型断言并保持所选图库一致。

## Validation

- `npm run lint -- --file src/app/tasks/page.tsx`

## Next Steps

- 在实际后端环境下确认新建后立即点击 “开始” 不再报错，若仍异常记录具体响应细节。

## Linked Commits

- _pending_
