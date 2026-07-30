## User Prompt

继续完成 Canon 状态门禁与长篇小说质量闭环，通过正式系统链路生成并验收全新 48 章小说。

## Goals

- 让每项 typed knowledge grant 都由正文中的明确 Canon 角色获知句支持。
- 保持来源事件绑定严格、可核验，同时消除 Prompt 与验证器对子片段语义的不一致。
- 在恢复真实付费生成前完成 focused、完整质量测试和仓库契约检查。

## Changes

- 将连续、逐字的角色获知证据视为对应事件证据片段内的合法子片段，不再要求等于整个事件片段。
- 为每项当前章 knowledge grant 生成 Canon 名称冻结的 `required_prefix`，要求正文逐字以 `Canon entity.name + 确认` 开始独立获知句。
- 明确禁止模型用自造姓名或职位别称替换 Canon 名称。
- 同步正文、状态提取和证据返修 Prompt 的来源事件绑定措辞。
- 增加事件子片段绑定与通用 Canon 职位名冻结回归测试。

## Validation

- `pytest -q tests/unit/test_story_novel_knowledge_evidence.py ... --no-cov`: 37 passed。
- `pytest -q tests/unit/test_story_novel_*.py tests/unit/services/test_narrative_memory_*.py --no-cov`: 474 passed, 1 skipped。
- 精确 `isort --check-only`: passed。
- 精确 `black --check`: passed。
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed。
- `git diff --check`: passed。
- 真实 Task 6650 正确 fail-closed，未把不合格状态写入当前状态；调用 #1410–#1415 均已终止。
- Docker 恢复前 Redis `celery` 队列长度为 0；服务启动仍等待用户明确授权。

## Next Steps

- 获得授权后恢复 backend、Celery worker、frontend 和 nginx。
- 从正式 UI 重新生成第 1 章并核验知识证据、状态、Narrative Memory 与 hash。
- 至少完成两章后执行正式 cancel、hash 快照和 Resume，再继续到 48/48 与 GPT-5.6 审读。

## Linked Commits

- Pending
