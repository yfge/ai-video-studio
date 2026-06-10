---
id: 2026-06-10T10-55-00Z-shared-generation-task-tracker
date: "2026-06-10T10:55:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - infrastructure
  - task-polling
related_paths:
  - ai-pic-frontend/src/hooks/useGenerationTaskTracker.ts
  - ai-pic-frontend/src/components/features/episode/useTimelineClipGenerationTaskTracker.ts
  - ai-pic-frontend/tests/generationTaskTracker.test.ts
summary: 将片段级任务轮询 hook 泛化为共享 useGenerationTaskTracker（任意 kind、labels 注入、onCompleted 携带最终 Task payload），clip tracker 改为薄包装，旧测试零修改通过。
---

# Shared Generation Task Tracker

## User Prompt

生产链路优化 Phase A 第二步：把上一轮为片段生成做的轮询 hook 泛化成全局共享 hook，供剧本/剧集/流水线/环境图等所有异步生成流程复用。

## Goals

- 新建 `src/hooks/useGenerationTaskTracker.ts`：kind 泛型化、labels 注入（Record 或函数）、`onCompleted(kind, taskId, task)` 携带最终 Task payload（供解析 `result_file_path` 如 `script:{id}`）、clipId 泛化为 contextId。
- 定时器管理、卸载清理、transient 错误重试、processing 升级逻辑原样保留。
- `useTimelineClipGenerationTaskTracker` 改薄包装：contextId→clipId 字段映射、原类型与 label helper re-export，3 个既有测试零修改通过。

## Changes

- 新增 `src/hooks/useGenerationTaskTracker.ts`（含 `isGenerationTaskActive` helper、`isActive(kind)` 返回值）。
- 重写 `useTimelineClipGenerationTaskTracker.ts` 为 ~100 行包装（保留 `ClipGenerationTaskKind/Phase/Map`、`clipGenerationTaskKindLabel`、`isClipGenerationTaskActive` 导出签名）。
- 新测试 `tests/generationTaskTracker.test.ts`：4 个用例（完成回调携带 payload、双 kind 独立跟踪、超时、同 kind 替换取消旧轮询）。
- 修复 lint 限制：Task 类型走 `@/utils/api/types` barrel 导入。

## Validation

- `npm run test`：66 个测试全部通过（含旧 tracker 3 个测试零修改）。
- `npm run lint`：0 errors。

## Next Steps

- A3：async 剧本生成接入 tracker + 完成自动选中新剧本。

## Linked Commits

- This commit.
