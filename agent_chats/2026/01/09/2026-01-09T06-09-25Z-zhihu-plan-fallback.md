---
id: 2026-01-09T06-09-25Z-zhihu-plan-fallback
date: "2026-01-09T06:09:25Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, story, novel-export, fix]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_export_payload.py
  - ai-pic-backend/app/services/story/story_novel_export_planner.py
  - ai-pic-backend/app/services/story/story_novel_export_zhihu.py
  - ai-pic-backend/app/utils/json_utils.py
  - ai-pic-backend/tests/unit/services/story/__init__.py
  - ai-pic-backend/tests/unit/services/story/test_story_novel_export_planner.py
  - ai-pic-backend/tests/unit/test_story_parser.py
summary: "Prevent Zhihu novel export failures when plan JSON is malformed/empty"
---

## User Prompt

导出知乎体小说失败，任务提示：`小说大纲解析失败（chapters为空）`，需要修复并提交。

## Goals

- 大纲（plan）解析失败时不再让导出任务直接失败。
- 降低大纲生成阶段因上下文过长导致的 JSON 不合规概率。
- 补充单元测试与端到端验证，确保导出可完成并可下载。

## Changes

- 强化 `extract_json_block`：在严格 JSON 解析失败时，增加去尾逗号、YAML 与 Python literal 的兜底解析。
- 为大纲生成增加“瘦身版 story payload”，减少 episodes/characters 传入长度，提高模型按 schema 输出的稳定性。
- 大纲生成失败时使用本地兜底大纲（保证 chapters 数量正确）继续后续章节生成流程。
- 新增单元测试覆盖大纲兜底逻辑与 JSON 解析兜底用例。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- Chrome (MCP/DevTools):
  - 登录 `geyunfei` / `Gyf@845261`
  - 打开故事 `ChromeE2E-TV-20260108-01`
  - 创建知乎体导出任务（目标字数 10000，章节数 3），观察任务从“大纲生成”推进到章节生成并最终完成（任务 536）
  - 点击“下载 .txt”，确认下载接口 `GET /api/v1/stories/novel/tasks/536/download` 返回 200

## Next Steps

- 若仍有偶发 JSON 不合规，考虑记录 plan 原始输出（截断后）到日志/任务详情，便于线上排障。
- 统计兜底大纲触发次数，评估是否需要进一步收敛 prompt/schema。

## Linked Commits

- (this commit)
