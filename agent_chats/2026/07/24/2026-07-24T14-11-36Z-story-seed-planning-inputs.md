---
id: 2026-07-24T14-11-36Z-story-seed-planning-inputs
date: "2026-07-24T14:11:36Z"
participants: [user, codex]
models: [gpt-5.6-sol]
tags: [backend, frontend, story-seed, novel, planning, model-selection]
related_paths:
  - ai-pic-backend/app/schemas/story_seed.py
  - ai-pic-backend/app/api/v1/endpoints/stories/story_seed.py
  - ai-pic-backend/app/api/v1/endpoints/stories/novel_task_queue.py
  - ai-pic-backend/app/services/story/story_seed_structure_service.py
  - ai-pic-backend/app/services/story/story_novel_task_processor.py
  - ai-pic-frontend/src/components/features/stories/StorySeedPlanningInputs.tsx
  - ai-pic-frontend/src/components/features/stories/StorySeedSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelLengthPanelBody.tsx
summary: Add explicit chapter-count and model selection to StorySeed structuring while preserving a separate prose model choice.
---

## User Prompt

AI 生成结构化章节时应当可以输入章节数，同时需要可以选择模型。

## Goals

- 让章节数在 StorySeed 结构化步骤显式输入，并作为模型输出覆盖合同。
- 让规划模型和小说正文模型分别从当前可用文本模型中选择。
- 将结构化任务的章节数和模型冻结到任务参数，并在生成结果中持久化以支持刷新恢复。
- 保持正文 Revision 的章数只来自已确认结构化大纲，不恢复正文独立章数输入。

## Changes

- `structure-async` 新增向后兼容的请求体，接受无应用级上限的正整数
  `chapter_count` 和可选 `model`。
- 任务参数与 Celery payload 冻结请求值；worker 优先使用请求模型，并要求输出
  位置严格覆盖 `1..chapter_count`。
- 结构化结果保存 `requested_chapter_count` 与实际 `planning_model`，手工编辑、
  确认和页面刷新均继续保留。
- StorySeed 面板新增章节数输入与规划模型下拉；已有结构化结果会恢复这两个值。
- 小说长度面板把正文模型自由文本改为可用模型下拉，仍独立保存到当前 Revision。
- 共享模型选择器补充可访问名称，便于真实操作和回归测试精确定位。

## Validation

- 后端精确四文件：11 passed。
- `pytest tests/unit/test_story_novel_*.py tests/unit/test_story_seed_*.py -q --no-cov`
  -> 375 passed, 1 skipped。
- 前端受影响三文件：5 passed。
- 完整 Story/Novel 前端集合：43 passed。
- `npm run lint` -> 0 errors，3 个既有 warnings。
- `npm run test` 已执行；本次相关失败已修复，剩余失败均位于既有
  Production Canvas 测试（其 planning settings fixture 与自动执行断言），不属于本切片。

## Next Steps

- 完成格式、仓库契约和生产构建后提交本切片。
- 在正式 UI/API 中使用 48 章与所选模型创建全新结构化 StorySeed，再继续真实长篇生成、
  cancel/resume 和 GPT-5.6 验收。

## Linked Commits

- Pending
