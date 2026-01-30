---
id: 2026-01-08T06-41-15Z-story-format-prompts-zhihu-novel-export
date: 2026-01-08T06:41:15Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, prompts, story, novel, e2e]
related_paths:
  - ai-pic-backend/app/prompts/template_resolver.py
  - ai-pic-backend/app/prompts/manager.py
  - ai-pic-backend/app/schemas/generation_requests.py
  - ai-pic-backend/alembic/versions/2a6b1c0d9f01_add_story_format_to_stories.py
  - ai-pic-backend/app/services/story/story_generation_service.py
  - ai-pic-backend/app/utils/story_parser.py
  - ai-pic-backend/app/api/v1/endpoints/stories/novel.py
  - ai-pic-backend/app/services/story/story_novel_export_service.py
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelExportSection.tsx
  - ai-pic-frontend/src/components/features/stories/StoryBasicsSection.tsx
  - ai-pic-frontend/src/utils/storyOptions.ts
  - README.md
  - README_EN.md
summary: "按 story_format 分流提示词，并新增故事导出知乎体小说（异步任务+下载）"
---

## User Prompt

- 现在对于不同类型的剧本和故事的生成，提示词是不是统一的？短剧及影视剧要把提示词分开管理。
- 使用 chrome 测试；故事现在为空了。
- 根据系统现状整体更新中英文 README。
- 加一个功能：把故事可以导成 1–3 万字左右的知乎体小说（agent 方式/异步任务）。

## Goals

- 支持按 `story_format`（短剧/电视剧/电影）选择不同提示词模板，便于分开管理。
- 修复“异步生成后故事为空/任务卡住”的实际问题，保证可用的端到端流程。
- 提供“故事→知乎体小说（10k–30k 字）导出”能力：创建任务、轮询进度、下载 txt。
- 更新中英文 README 以匹配当前系统行为与入口。

## Changes

- Backend：新增 `story_format` 字段并在 Prompt 渲染时自动解析 `*_tv_series`/`*_film` 模板变体；Story 生成逻辑增加对嵌套 JSON/代码块的解析兜底。
- Backend：新增故事“知乎体小说”异步导出（Task + Celery），支持下载生成文件；修复 worker 与 stories 模块的导入耦合导致任务不执行的问题；优化大纲 JSON 可解析性（避免字符串内真实换行）并在导出时还原 `\\n` 为真实换行。
- Frontend：故事生成面板增加“故事形态”选择；新增故事详情“导出知乎体小说”面板（创建任务、显示进度、下载 txt）。
- Docs：更新根目录 `README.md` / `README_EN.md` 以及 docker 文档，补充 story_format 分流与小说导出入口。

## Validation

- Backend tests: `pytest -q tests/unit/test_story_format_prompt_templates.py tests/unit/test_story_parser.py`
- Frontend lint: `cd ai-pic-frontend && npm run lint`
- Chrome E2E（http://localhost:8089）：
  - 登录后在“故事创作”页创建异步故事任务，任务完成后故事详情页字段不为空。
  - 在故事详情页创建“知乎体小说”导出任务（10k 字、5 章），任务完成后可点击“下载 .txt”，网络请求 `GET /api/v1/stories/novel/tasks/{task_id}/download` 返回 200，文件内容换行正常。

## Next Steps

- （可选）为历史数据中 synopsis 包含 ```json 的旧故事提供一次性修复/回填脚本或管理入口。
- （可选）任务列表页识别 `result_file_path` 前缀（如 `novel_file:` / `story:`）并提供跳转/下载动作。

## Linked Commits

- N/A（本次未提交 commit）
