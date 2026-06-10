---
id: 2026-06-10T10-30-00Z-toast-notification-provider
date: "2026-06-10T10:30:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - notifications
  - infrastructure
related_paths:
  - ai-pic-frontend/src/components/shared/notifications/ToastProvider.tsx
  - ai-pic-frontend/src/components/shared/notifications/toastTypes.ts
  - ai-pic-frontend/src/app/layout.tsx
  - ai-pic-frontend/tests/toastProvider.test.tsx
summary: 新增非阻塞 toast 通知系统（右上角栈、自动消失、ARIA），作为生产链路统一任务反馈基础设施第一步；NotifyVariant 类型上收到 shared 层。
---

# Toast Notification Provider

## User Prompt

整体优化生成链路使 IP/故事/剧集/剧本/分镜生产级可用；已批准计划 Phase A 第一步：建非阻塞 toast 系统，替代"任务已提交"类阻塞 modal（每次要点确定）。

## Goals

- 新增 `ToastProvider` + `useToast().notify(message, variant, opts?)`，与现有 `AlertModalProvider`（保留给确认/阻断场景）并存。
- 右上角固定栈（z-2100 高于 modal 的 2000），最多 5 条，success/info 5s、warning 7s、error 8s 自动消失 + 手动关闭。
- 无障碍：容器 `aria-live="polite"`，error 用 `role="alert"`，其余 `role="status"`。
- `NotifyVariant` 类型从 episode feature 层上收到 `shared/notifications/toastTypes.ts`（后续共享 hook 不反向依赖 feature 层）。

## Changes

- 新增 `src/components/shared/notifications/`：`ToastProvider.tsx`（context + 栈管理 + 定时器清理）、`toastTypes.ts`（NotifyVariant、时长常量、栈上限）、`index.ts`。
- `src/app/layout.tsx`：`ToastProvider` 挂载在 `AlertModalProvider` 内层。
- `TimelineClipProviderReworkControlsTypes.ts`：`NotifyVariant` 改为 import + re-export，调用方零改动。
- 新测试 `tests/toastProvider.test.tsx`：5 个用例（variant→role 映射、自动消失、手动关闭、5 条栈上限、可选标题）。

## Validation

- `npm run test`：62 个测试全部通过。
- `npm run lint`：0 errors。
- `npm run build`：通过（修复 re-export 局部作用域类型错误后）。

## Next Steps

- A2：泛化 `useGenerationTaskTracker` 共享 hook。
- A3-A8：各生成流程接入 toast + 轮询 + 完成自动刷新。

## Linked Commits

- This commit.
