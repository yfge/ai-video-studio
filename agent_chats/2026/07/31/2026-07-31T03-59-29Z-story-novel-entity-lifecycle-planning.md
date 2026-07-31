## User Prompt

用户确认四条成长曲线只作为全书软规划与最终吸引力评审，不得成为逐章数值 KPI；继续修复新版长篇真实运行暴露的规划连续性问题。

## Goals

- 保持认知、能力、资源、活动/时间尺度为可选软曲线。
- 修复持久实体已经在早期章节实际使用、却在后续章节才被计划成“首次创建”的状态链错误。
- 不放宽 Canon、状态或未来剧情门禁，不加入题材专用词或逐章升级模板。

## Changes

- 章节规划 Prompt 要求初态为不存在的持久实体在首次实际使用章建立唯一创建状态，后续只能从当前状态升级、扩展、转交或终止。
- 独立计划语义审计现在接收 Canon entity aliases、精确不存在字面值和初始状态，并能把错误的后置首次创建替换为连续状态升级。
- `plan_semantic_audit_version` 从 2 升至 3，新规则只冻结到新规划，不迁移旧 Revision。
- 新增共同账本别名、首次使用与错误后置创建替换的回归测试。

## Validation

- `pytest --collect-only -q tests/unit/test_story_novel_plan_entity_lifecycle_prompt.py tests/unit/test_story_novel_planning_location_repair.py tests/unit/test_story_novel_planning_batches.py` -> 9 collected。
- `pytest -q --no-cov tests/unit/test_story_novel_plan_entity_lifecycle_prompt.py tests/unit/test_story_novel_planning_location_repair.py tests/unit/test_story_novel_planning_batches.py` -> 9 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov` -> 859 passed, 1 skipped。
- 精确路径 `isort`、`black` 与 `git diff --check` 通过。
- `python run_tests.py quick` 未进入测试：包装器强制联网安装 `requirements-test.txt`，受限网络无法解析 PyPI；未修改全局 Python 环境，完整 Story Novel 单测已覆盖本次领域变更。

## Next Steps

- 从同一冻结 StorySeed 新建 Revision，使语义审计 v3 重新规划完整 48 章；旧 Revision 保留为失败证据。
- 使用正式 UI/API 和真实 MySQL 生成，完成 cancel/resume hash 复核、连续性检查、GPT-5.6 分批与全书审读、DOCX 导出和审批。

## Linked Commits

- This commit.
