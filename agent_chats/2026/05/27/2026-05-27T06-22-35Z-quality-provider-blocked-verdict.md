## User Prompt

继续推进质量验证，不要把 provider 额度/欠费问题混成内容质量结论。

## Goals

- 在 10 条样片质量报告里单独暴露 provider 计费/额度阻断。
- 当样片因为 Seedance 欠费/额度失败而无法评价时，给出明确 verdict。
- 保持测试和契约检查可复跑。

## Changes

- `aggregate_quality_report` 增加 `provider_billing_or_quota_error_count`。
- 质量报告 checks 增加 `provider_billing_or_quota_errors_zero`。
- 如果最终样片包含 `provider_billing_or_quota_failed`，verdict 改为 `provider_blocked_not_evaluable`。
- 新增聚合测试覆盖 10 条样片全被 provider billing/quota 阻断的场景。

## Validation

待本 commit 前统一执行 targeted tests、docs/contracts 与 `git diff --check`。

## Next Steps

- 修复 Volcengine 账号欠费/额度后，重新跑 `--mode live-10`。
- 如果 provider 恢复后稳定性仍不足，再继续处理 prompt、角色参考图、Seedance 参数和重试策略。

## Linked Commits

Pending
