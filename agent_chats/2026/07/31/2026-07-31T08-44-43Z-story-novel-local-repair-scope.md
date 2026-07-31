## User Prompt

用户要求世界事件、人物记忆只用于规划，并要求正文按当前章节需要逐步扩展人物、地点和世界，不把未来或其他段落的合同泄露给当前正文。

## Goals

- 局部返修只读取失败 block 已绑定的当前事件、角色和 proof contracts。
- 防止单个 replacement 因看到全章事件而重写整章。
- 保留其他 blocks 字节不变和全章状态/未来审计。

## Changes

- `build_repair_input` 按失败 beat 的 `bound_event_ids` 和 `allowed_entity_ids` 裁剪 `current_chapter_context`。
- 局部返修不再接收全章 `typed_execution_boundary`；精确效果由 `current_contract_requirements.proof_contracts` 提供。
- Prompt 明确 proof contracts 是本次返修唯一必须兑现的效果合同，不得扩写其他事件。
- 新增跨 beat 隔离回归，证明 B01 不会看到 B02 的事件、演员或全章执行边界。

## Validation

- 真实 Task `#6899`：B01 只绑定 `event-10-1` 和陈禾，但旧返修输入暴露全章 3 个事件，响应实际出现东方浪和“铲”动作；两次 replacement 为 2,385/1,532 字符，任务正确 fail-closed。
- 首轮 targeted 暴露补丁函数返回块位置错误（2 failed, 34 passed），恢复函数边界后同一集合 36 passed。
- `cd ai-pic-backend && pytest tests/unit/test_story_novel_*.py -q --no-cov` -> 868 passed, 1 skipped。
- 精确 black/isort、repo contracts diff 和 `git diff --check` -> passed。

## Next Steps

- 重启 Worker，从第 10 章 repair-only Resume，验证模型只完成 `event-10-1` 且 replacement 落入预算。
- 继续完成 48/48、连续性、GPT-5.6 评审、DOCX 和审批。

## Linked Commits

- This commit: `fix(story): isolate local repair contracts`
