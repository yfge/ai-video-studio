---
id: 2026-01-08T10-46-51Z-story-novel-exports-history
date: 2026-01-08T10:46:51Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, stories, novel-export]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories/novel.py
  - ai-pic-backend/app/schemas/story_novel_export.py
  - ai-pic-backend/tests/test_story_novel_exports_list_api.py
  - ai-pic-frontend/src/utils/storyNovelApi.ts
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelExportsHistory.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelExportSection.tsx
summary: "新增故事小说导出历史列表，刷新后无需 localStorage 也能预览/下载"
---

## User Prompt

- “如果没有 localStorage 呢？”
- “小说生成后页面上怎么查看（增加）”

## Goals

- 刷新后仍能从故事详情页找到最近的小说导出任务并进行预览/下载（不依赖本地存储保存 task_id）。
- 保持前后端接口一致，权限隔离正确（非管理员仅能看到自己的导出记录）。

## Changes

- Backend: 新增 `GET /api/v1/stories/business/{story_business_id}/novel/exports` 返回导出历史（按 id 倒序，支持 limit，非管理员按 user_id 过滤）。
- Backend: 新增 `StoryNovelExportSummary/StoryNovelExportListResponse` schema，列表接口不返回正文内容。
- Frontend: 新增 `StoryNovelExportsHistory`，在故事详情“导出知乎体小说”区域展示最近导出记录并支持预览/下载。
- Frontend: 新增 `listStoryNovelExports()` API；导出下载/预览的 token 读取增加 try/catch，避免 localStorage 异常导致函数抛错。

## Validation

- Frontend: `cd ai-pic-frontend && npm run lint`（通过，仅有既有 warning）。
- Backend: 运行全量 `pytest`，存在大量既有失败用例；本次新增相关用例 `tests/test_story_novel_exports_list_api.py` 在输出中通过。
- Chrome (MCP): 打开 `http://localhost:8089/stories/bd296c67e771472bace4734305d61afb`，刷新后在“历史导出”看到 task 530/525；点击“预览全文”弹窗显示正文，关闭后页面正常。

## Next Steps

- 若需要“刷新后继续查看未完成任务进度”，建议补一个按 `Task.target_business_id` 查询的“小说导出任务”列表接口（可覆盖 processing 状态）。
- 视产品需要，历史导出列表可增加“显示更多/删除记录/按风格筛选”等能力。

## Linked Commits

- (not committed)
