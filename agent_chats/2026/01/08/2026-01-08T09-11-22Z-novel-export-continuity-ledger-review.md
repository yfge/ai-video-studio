---
id: 2026-01-08T09-11-22Z-novel-export-continuity-ledger-review
date: 2026-01-08T09:11:22Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, story, agent, novel]
related_paths:
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter.txt
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter.yaml
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter_rewrite.txt
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter_rewrite.yaml
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_ledger_update.txt
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_ledger_update.yaml
  - ai-pic-backend/app/services/story/story_novel_export_continuity.py
  - ai-pic-backend/app/services/story/story_novel_export_service.py
  - ai-pic-backend/app/services/story/story_novel_export_zhihu.py
  - ai-pic-backend/tests/unit/test_story_novel_export_continuity.py
summary: "Zhihu 小说导出：连贯性账本 + 每章两段式审稿，并增强大纲 JSON 稳定性"
---

## User Prompt
连贯性账本 + 每章两段式审稿。

## Goals
- 生成时跨章携带“连贯性账本（facts/timeline/人物状态/线索）”，避免设定漂移。
- 每章采用“草稿 → 润色/一致性修订”两段式，提高可读性与一致性。
- 修复/降低“小说大纲解析失败（chapters为空）”的概率，保证任务可稳定完成。

## Changes
- 新增/调整知乎体小说导出模板，加入 `ledger`、`previous_tail`、章节润色与账本更新模板。
- 后端导出流程：
  - 生成 `plan` 后按章循环：草稿 → 润色 → 账本更新 → 维护 `running_summary` 与 `previous_tail`。
  - `plan/ledger_update` 统一使用严格 JSON system prompt，并对 `plan` 做一次自动重试。
  - 修复 `ledger_update` 缺失时不应重置账本；并改进章节末尾标记解析，避免“【本章小结/卡点】”被模型放在章节开头导致重复标记。
- 补充单元测试覆盖：标记解析/纠正、账本更新 payload 归一化、模板渲染不缺参。

## Validation
- Backend pytest（定向）：
  - `cd ai-pic-backend && pytest -q tests/unit/test_story_novel_export_continuity.py tests/unit/test_story_novel_export_payload.py tests/test_story_novel_exports_db.py`
- Chrome E2E（本地 dev 环境）：
  - 登录后进入 `http://localhost:8089/stories/bd296c67e771472bace4734305d61afb`，创建知乎体小说导出任务（task_id=530）。
  - 观察进度出现“生成正文草稿 / 润色与一致性检查”等阶段。
  - 点击“下载 .txt”，确认网络请求 `GET /api/v1/stories/novel/tasks/530/download` 返回 200。
  - DB 校验：`tasks.id=530` 为 `COMPLETED`，且 `story_novel_exports.task_id=530` 记录存在并包含 `content_text`。
- Worker 热更新：重启 `ai-video-celery-worker` 以加载最新代码。

## Next Steps
- 若仍出现 plan JSON 不稳定，可考虑新增专用 `story_novel_zhihu_plan_repair` 提示词（对失败输出做结构化修复），进一步提升成功率。
- 若需要进一步提升质量：可把 `ledger` 与 `running_summary` 做更强的结构化（例如按人物/线索分区、长度预算）并加入“章节自检清单”。

## Linked Commits
- N/A（本次未提交）

