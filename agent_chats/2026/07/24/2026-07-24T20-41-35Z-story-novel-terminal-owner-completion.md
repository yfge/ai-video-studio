## User Prompt

完成 Canon 状态门禁与长篇小说质量闭环；结构化章节生成需要可输入章节数并选择模型，真实链路门禁失败时保持严格校验并做最小修复。

## Goals

- 修复真实 Task 6635 暴露的模型 Canon 终态物件遗漏 `owner_id=null` 问题。
- 只在模型解析路径补齐可由既有 typed status 确定推导的 owner 清空。
- 保持原始 Canon、冲突 owner、未来状态及重复 outcome 的严格拒绝。
- 提升模型 Canon filter 版本，使旧 checkpoint 重新编译。

## Changes

- 将终态物件状态字面值集中到共享 location/state 常量。
- `story_novel_canon_milestone_filter` v3 对非重复、有计划章节、object、明确终态且没有任何 owner outcome 的 milestone，确定性追加一条 `owner_id eq null`。
- 记录 `terminal_owner_clear_completed` diagnostic；已有 owner outcome 时不自动覆盖或添加。
- 新增八项回归，覆盖补齐、raw strict、已正确输入、非终态、非物件、冲突 owner、初态提前满足及后续归档保持不变。

## Validation

- `pytest -q --no-cov tests/unit/test_story_novel_terminal_owner_filter.py tests/unit/test_story_novel_canon_milestone_filter.py tests/unit/test_story_novel_milestone_outcomes.py`：22 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：394 passed, 1 skipped。
- 精确路径 `pre-commit run isort`：passed。
- 精确路径 `pre-commit run black`：passed。
- `python scripts/check_repo_docs.py`：ok。
- `python scripts/check_repo_contracts.py --mode diff <changed files>`：ok。
- `git diff --check`：passed。
- `./docker/build_prod_images.sh`：passed；dirty-worktree build 使用 HEAD tag
  `d396bed2`，backend manifest
  `sha256:05f3351d2c1e9f276e41bc4f1687df12304224ac48000beb6207a9ddb8d7f2de`，
  frontend manifest
  `sha256:a6e88f4a0f91f04499f8b9cf6534670ca7e9d67855079f6e9a2fee59bdb8e864`。

## Next Steps

- 构建生产镜像并加载当前源码。
- 仅对当前验收 Revision 走一次正式 Resume，确认新 Canon diagnostic、计划和章节门禁。
- 达到至少两章后执行正式 cancel/hash snapshot/Resume，再继续 48/48 与 GPT-5.6 审读。

## Linked Commits

- Pending
