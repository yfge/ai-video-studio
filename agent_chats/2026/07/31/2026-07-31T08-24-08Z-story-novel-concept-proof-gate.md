## User Prompt

用户确认全书成长采用认知、能力、资源、活动/时间尺度四条软曲线，并要求世界中的人物、地点、组织和概念按剧情需要依次扩展，不把内部规划术语写成逐章硬性标准。

## Goals

- 保留人物、地点、组织和关键物件的具名首次登场约束。
- 抽象概念改由当前章事件 proof 与语义审计证明，不要求正文逐字包含内部 Canon 标签。
- 用真实运行证据验证长度控制、局部返修和 checkpoint 边界。

## Changes

- `story_novel_v3_gate.py` 跳过 `kind=concept` 的逐字名称门禁；其他实体类型保持原行为。
- 增加回归测试，证明自然语言已经表达概念时无需复述内部标签。
- 真实 Task `#6897` 的第 7 章首稿已在 2,000–3,000 字符合同内，但因概念标签逐字门禁触发整章局部返修；第 8 章无局部返修直接通过。任务通过产品入口取消，保留 8/48 ready checkpoint。

## Validation

- `cd ai-pic-backend && pytest -q tests/unit/test_story_novel_v3_prose_integrity.py --no-cov` -> 7 passed。
- `cd ai-pic-backend && pytest tests/unit/test_story_novel_*.py -q --no-cov` -> 866 passed, 1 skipped。
- `pre-commit run black --files ...` -> passed。
- `pre-commit run isort --files ...` -> passed。
- `python scripts/check_repo_contracts.py --mode diff ...` -> passed。
- `git diff --check -- ...` -> passed。
- 真实 MySQL：Task `#6897` 为 `CANCELLED`，Revision `38a8d8eee1744c2689eabaf29a5cc2ba` 保留 8 个 ready 章节；第 7 章 2,397 字符，第 8 章 2,202 字符。

## Next Steps

- 重启 Celery Worker 加载门禁修复，从第 9 章正式 Resume。
- 完成 48/48、连续性检查、GPT-5.6 分批/全书评审、DOCX 和审批证据。

## Linked Commits

- This commit: `fix(story): prove concepts through events`
