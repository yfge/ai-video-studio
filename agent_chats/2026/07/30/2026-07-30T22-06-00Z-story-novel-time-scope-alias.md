## User Prompt

用户确认成长曲线只作为全书软方向，并要求继续完成真实长篇生成。

## Goals

- 保持当前 Revision 的冻结 Prompt 不变。
- 让章前规划模型输出的非权威 `time_scope=current_chapter` 能进入既有严格枚举合同。
- 不放宽 Canon、未来剧情、状态、知识或时间连续性门禁。

## Changes

- 在既有 execution contract 模型别名归一入口，将 `current_chapter` 保守归一为 `unspecified`。
- 扩展相邻单元测试，证明合法别名归一后仍经过原严格 validator。

## Validation

- `pytest -q --no-cov tests/unit/test_story_novel_chapter_package_observed_aliases.py` -> 4 passed。
- `pytest -q --no-cov tests/unit/test_story_novel_*.py` -> 843 passed, 1 skipped。
- 精确文件 `isort`、`black`、repo contracts diff 与 `git diff --check` 均通过。

## Next Steps

- 验证通过后重载 backend/worker，并通过产品 UI 从第 32 章正式 Resume。

## Linked Commits

- 本记录与修复同一原子提交。
