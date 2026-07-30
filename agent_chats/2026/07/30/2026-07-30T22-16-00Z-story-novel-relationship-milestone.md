## User Prompt

用户确认全书成长曲线为软方向，并要求继续真实 48 章生成与最终质量验收。

## Goals

- 修复第 32 章正式伙伴关系里程碑无法从 Canon 编译为 typed state 的问题。
- 保持 Canon 里程碑、状态校验和 future gate fail-closed。

## Changes

- 让 Canon `contains` outcome 同时支持 JSON 数组和明确的 `关系标签:角色ID` 关系映射。
- 关系映射只写入对应角色 ID；其他非数组 `contains` 继续拒绝。
- future milestone 投影、实际 effect 编译和 consumed outcome 验证共享同一语义。

## Validation

- 相关里程碑、状态编译和别名测试 -> 23 passed。
- `pytest -q --no-cov tests/unit/test_story_novel_*.py` -> 845 passed, 1 skipped。
- black 修改测试文件后已复跑；最终 black、isort、repo contracts diff 与 `git diff --check` 均通过。

## Next Steps

- 验证通过后重载 backend/worker，通过产品 UI 从第 32 章 Resume。

## Linked Commits

- 本记录与修复同一原子提交。
