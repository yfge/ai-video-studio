## User Prompt

用户接受四条可选成长曲线作为全书软规划和吸引力评审维度，并要求完成真实长篇生成。

## Goals

- 保持成长曲线为软方向，不增加逐章升级 KPI。
- 减少章前规划模型因 execution contract 枚举误写导致的无意义格式返修。

## Changes

- 明确 `time_scope` 与 `effort` 的合法枚举。
- 明确具体日期只通过 `timeline_ids` 绑定，禁止写入 `time_scope`。
- 增加提示词合同回归断言，不放宽现有确定性 validator。

## Validation

- `pytest -q tests/unit/test_story_novel_format_repair_prompt.py tests/unit/test_story_novel_continuity_watchpoints.py --no-cov` — 6 passed.
- Exact-path isort and black hooks passed.
- `check_repo_contracts.py --mode diff` passed for the prompt, test, and ledger.
- Exact-path `git diff --check` passed.

## Next Steps

- 重启 backend/worker 加载提示词后，通过正式 Resume API 继续 v32。
- 验证已完成两章的 body/source/context/state hash 保持不变。

## Linked Commits

- Pending.
