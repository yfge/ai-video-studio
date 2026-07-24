## User Prompt

继续完成 Canon 状态门禁与长篇小说质量闭环；结构化章节可输入章数并可选择模型，使用系统真实链路生成 48 章并完成断点恢复和 GPT-5.6 验收。

## Goals

- 让显式 48 章结构化大纲可以在 provider 有限单次输出能力下编译成完整 typed 章节合同。
- 保持 Canon、状态、未来里程碑、地点与伏笔门禁 fail closed，不通过放宽 validator 绕过错误。
- 规划过程按批 checkpoint，任务失败或取消后可以复用已验证的计划前缀。
- 修正物件所有权变化与持有者移动造成的冗余地点转移。

## Changes

- 将显式章节合同按最多 8 章一批生成；每批只包含本批冻结大纲和已验证前缀状态，不重复发送历史章节合同。
- 每批使用原有 Pydantic、冻结大纲合并和 Canon 状态校验；最终批仍执行完整全书确定性验证。
- 每批 checkpoint `chapter_plan_draft` 与 Canon hash，Resume 只复用连续且重新验证通过的前缀。
- 规划修复提示改为精确批次范围，保留每批一次有界修复。
- Canon 提示明确物件随 owner 移动时不得把更早已满足的地点写成未来 milestone outcome；此类失败在 Resume 时重新编译 Canon。
- 规划归一化删除新持有者已携带的重复物件 movement 和同地点 no-op movement。
- 新增 48 章分批、计划断点恢复、所有权派生地点回归测试；更新 outline merge monkeypatch 到拆分后的 parser。

## Validation

- 真实失败证据：Revision `1fe57d4e72dd45f19281c3c524c2fbce`，Task `#6617` / `8f7e94986ac0425da8d77746c59afdae`。
- Invocation `#1246`：DeepSeek `deepseek-v4-pro`，`max_tokens=67200`，11,039 input / 7,916 output，`finish_reason=stop`，response hash `8f8ded8f7f75334b…`，JSON 在第 19 章中断。
- Invocation `#1247`：26,767 input / 11,008 cache / 27,349 output，`finish_reason=stop`，response hash `efc3a6ead6ebc0df…`；完整 48 章仍被三项物件地点门禁拒绝，正文保持 0 章。
- `pytest -q --no-cov tests/unit/test_story_novel_planning_batches.py tests/unit/test_story_novel_owner_location_normalization.py tests/unit/test_story_novel_outline_merge.py tests/unit/test_story_novel_planning_repair.py`：19 passed。
- `pytest -q --no-cov tests/unit/test_story_novel_*.py`：363 passed, 1 skipped。
- 精确路径 `isort`、`black`、`ruff`：passed。
- `python scripts/check_repo_contracts.py --mode diff <11 paths>`：ok。
- `python scripts/check_repo_docs.py`：ok。
- `git diff --check`：passed。

## Next Steps

- 重启 backend 和 Celery worker加载本提交。
- 仅对上述 Revision 调用一次正式 `resume-async`；核验重新编译 Canon 后的分批计划 checkpoint。
- 进入正文后在至少 2 个 ready 章执行正式 cancel、保存 MySQL hash 快照并 Resume 到 48/48。
- 完成连续性检查、GPT-5.6 八批审读和全书综合、审批、Canon 提升及最终 run artifact。

## Linked Commits

- Pending
