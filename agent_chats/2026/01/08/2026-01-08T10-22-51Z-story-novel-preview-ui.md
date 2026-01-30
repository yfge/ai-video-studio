---
id: 2026-01-08T10-22-51Z-story-novel-preview-ui
date: 2026-01-08T10:22:51Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, story, novel]
related_paths:
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelExportSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelPreviewButton.tsx
  - ai-pic-frontend/src/utils/storyNovelApi.ts
summary: "故事详情页：知乎体小说支持页面预览与复制全文，并记住上次导出任务"
---

## User Prompt

小说生成后页面上怎么查看；增加。

## Goals

- 在故事详情页直接查看已生成小说正文（不必下载文件才能阅读）。
- 支持一键复制全文。
- 解决页面刷新后丢失 task_id 的问题（至少能记住本故事上一次导出任务）。

## Changes

- 新增“预览全文”按钮：打开 Modal 拉取 `GET /api/v1/stories/novel/tasks/{task_id}/download` 的文本内容并展示；支持“刷新/复制全文/关闭”。（`ai-pic-frontend/src/components/features/story-detail/StoryNovelPreviewButton.tsx`）
- 新增 `fetchStoryNovelText()`：复用下载接口但直接读取 `text()`，用于预览与复制。（`ai-pic-frontend/src/utils/storyNovelApi.ts`）
- Story 页记住上次导出任务：以 `story_novel_export_task:{story_business_id}` 存储 task_id，刷新后自动恢复并继续轮询状态。（`ai-pic-frontend/src/components/features/story-detail/StoryNovelExportSection.tsx`）

## Validation

- Frontend lint：`cd ai-pic-frontend && npm run lint`
- Chrome E2E：
  - 登录后打开故事详情页 `http://localhost:8089/stories/bd296c67e771472bace4734305d61afb`
  - 在导出区块看到已完成任务 `task_id=530`，出现“预览全文/下载 .txt”
  - 点击“预览全文”弹出 Modal 并展示正文；点击“复制全文”提示成功；关闭 Modal

## Next Steps

- 如需“历史导出列表/多版本对比”，建议新增后端 list endpoint（按 story_business_id 返回 exports 列表）并在故事页展示。

## Linked Commits

- N/A（本次未提交）
