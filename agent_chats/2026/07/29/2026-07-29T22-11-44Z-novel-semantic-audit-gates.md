## User Prompt

用户要求放松时间门禁，不再强制正文逐字出现固定日期，并追问其他正文强制审计后，
要求按审计结论改造长篇小说生成链路。

## Goals

- 保留 required event、关键状态/权限、地点与知识来源的语义硬门禁。
- 取消 timeline、milestone 和 thread 的重复独立正文证明。
- 将日期、未来实体和自然语言世界规则的字符串命中降为审计候选。
- 让 audit 在不泄露给 prose 的前提下识别提前获得权限、所有权、知识或伏笔结果。

## Changes

- V3 `expected_delta` 的 proof contracts 只保留 event/state/location/knowledge；
  milestone 与 thread lifecycle 继续作为服务端确定性状态效果。
- timeline 从必填 proof contract 改为 `current_timeline` 语义上下文，允许合理相对时间、
  昼夜承接和省略重复日期。
- V3 prose 的确定性预检只保留篇幅；未来日期/实体与 world-rule 字符串不再直接失败，
  仍保留 legacy V2 原有门禁。
- 新增 audit-only current state contract 和 future state boundaries，只覆盖当前章相关主体，
  不含未来标题、goal 或 end_state；future card 的单实体命中仅用于提高审计召回。
- 审计输入合同版本升级为 5，旧 checkpoint 必须按新语义重审后才能复用。

## Validation

- Focused expected-delta/proof/future/semantic-audit tests：26 passed。
- V3、prose Canon 与 current-actor future gate tests：166 passed。
- 完整 `tests/unit/test_story_novel_*.py --no-cov`：747 passed, 1 skipped。
- `python run_tests.py quick`：exit 0。
- 精确 Python 路径 black/isort：通过。
- 精确 changed-path repo contracts diff 与 `git diff --check`：通过。

## Next Steps

- 重启挂载当前源码的 Docker dev backend/worker。
- 通过正式 UI/API 新建 V3 Revision，验证语义时间与 future-state audit 的真实模型表现。
- 完成 48 章、cancel/Resume/hash、连续性、GPT-5.6 审读和审批后再结束 active exec plan。

## Linked Commits

- Pending.
