---
id: 2026-01-08T12-44-12Z-zhihu-novel-export-length-fix
date: 2026-01-08T12:44:12Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, story, novel-export, prompts]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_export_zhihu.py
  - ai-pic-backend/app/services/story/story_novel_export_zhihu_chapter.py
  - ai-pic-backend/app/services/story/story_novel_export_planner.py
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_plan_compact.txt
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_plan_compact.yaml
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter_beats.txt
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter_beats.yaml
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter.txt
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter_finalize.txt
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter_finalize.yaml
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_chapter_rewrite.txt
  - ai-pic-backend/tests/unit/test_story_novel_export_chapter_count.py
summary: "修复知乎体小说导出少章与承接断裂：卡点传递 + 章节收尾兜底 + 单章节拍"
---

## User Prompt
- “我下截了一个 发现内容不全，是不是因为数据库的列的内容长度有了限制？”

## Goals
- 排除“DB 字段长度截断”的可能性，并解决实际的“导出字数/章节不足”导致的内容不全问题。
- 让导出更稳定地达到目标字数（1–3 万字），同时保持连贯性账本 + 每章两段式审稿的质量路径。

## Changes
- 新增紧凑版大纲模板 `story_novel_zhihu_plan_compact`：避免一次性输出过长的 `key_beats`（容易触发 max_tokens 导致大纲章节数不足）。
- 新增单章 beats 模板 `story_novel_zhihu_chapter_beats`：每章在写作前先生成 5-9 条可执行节拍，再进入“草稿→审稿→账本更新”链路。
- 新增 `StoryNovelExportPlanner` 辅助模块：
  - 生成紧凑大纲并规范化章节（补齐 chapter_number、分配 target_words、兜底 cliffhanger_hint）。
  - 生成单章 beats（失败重试 + 兜底 beats）。
- 修复导出记录的 `chapter_count`：改为实际生成的章节数（此前可能误写为大纲章节总数）。
- 生成链路不再在 `target_words * 1.05` 时提前停止，避免出现“计划 11 章但只生成前 3 章”的不一致。
- 兜底节拍：当 beats JSON 生成失败时，fallback beats 也会强制把 `previous_cliffhanger` 放到第一条，保证下一章能承接上一章卡点。
- `previous_cliffhanger` 优先使用 ledger 更新输出的 `chapter_cliffhanger`（更短、更可执行），避免用过长的“卡点段落”导致下一章忽略承接。
- 单章输出预算上调（`max_tokens` 更充足），减少“章节末尾被截断/半句话进小结”的情况。
- 新增 `story_novel_zhihu_chapter_finalize`：当模型未输出【本章小结/卡点】时自动补全收尾，保证结构完整。
- 重构：抽出单章生成逻辑到 `story_novel_export_zhihu_chapter.py`，保持服务文件 < 250 行限制。
- 增加单测：确保导出结果包含计划的全部章节标题（`—— 更新`）。
- 强化审稿提示词：要求“首次点名必须交代如何得知姓名”，并补足时间/地点过渡，降低阅读中的断裂与突兀信息跳跃。
- 章节承接强化：新增 `previous_cliffhanger` 传入每章 beats/正文/审稿提示词，要求开头 1-3 段必须承接上一章卡点，减少“明明有悬念但下一章跳场”的断裂。
- `build_plan_context()` 补充 `chapter_goal` 字段到 plan 上下文，便于每章在整体规划下推进。

## Validation
- Backend: `pytest -q tests/unit/test_story_novel_export_chapter_count.py tests/unit/test_story_novel_export_payload.py tests/unit/test_story_novel_export_continuity.py tests/unit/test_story_format_prompt_templates.py tests/test_story_novel_exports_db.py tests/test_story_novel_exports_list_api.py`（通过）。
- Frontend: `npm run lint`（通过；存在 Next.js lint warnings）。
- Chrome (MCP):
  - 登录 `geyunfei`，进入故事 `ChromeE2E-TV-20260108-01` 详情页。
  - 创建导出任务：target_words=10000、chapter_count=6、provider=DeepSeek（task `533`）。
  - 结果：任务完成显示 `完成：约 12492 字（6 章）`；下载文件 `uploads/exports/novels/zhihu_novel_ChromeE2E_TV_20260108_01_20260108T152114Z.txt` 含 6 个 `—— 更新` 标题。
  - 连贯性抽查：第 2 章开头承接第 1 章卡点（高层会议/伦理问题）；第 6 章开头承接第 5 章卡点（告警触发的服务故障），未再出现“半句话进小结”的截断问题。

## Next Steps
- 若要进一步提高“章节数稳定性”（例如固定 6/11/17 章输出），可把“达到目标字数即提前 break”的策略改为“固定生成到最后一章但控制每章字数上限”，并在最后一章做收束。
- 可在导出记录中存储 `planned_chapter_count`（大纲章节数）与 `actual_chapter_count`（实际生成），便于对齐 UI 展示与质量分析。

## Linked Commits
- (not committed)
