## User Prompt

继续完成真实系统 API + MySQL 的 48 章长篇生成；任何规划或质量门禁失败时停止付费，给出精确 delta，修复正确链路而不放宽 validator。

## Goals

- 修复 Task 6636 第 17–24 章语义复核把 18 个权威 event ID 折叠为
  8 个自造 `evt-*` ID 的规划阻断。
- 保持 `_parse_audit` 的全量、同序、唯一事件覆盖门禁不变。
- 让首轮与复核 prompt 都提供逐事件的不可改输出骨架。

## Changes

- 将语义审计 prompt 拆到独立小型模块，降低原 249 行热点。
- 把章节 key_events/required_event_ids 展平为 `event_contract`。
- 随 prompt 提供包含全部 position/event_id 的 `output_skeleton`，要求模型只填
  `missing_effects`，禁止按章合并或重命名事件。
- 删除容易诱导模型生成 `evt-1` 的静态示例；parser 和 typed-effect validator
  保持严格。

## Validation

- Task 6636 fail closed，0 章；精确错误：
  `章节计划语义审计事件覆盖不完整`，expected 18 events、actual 8。
- invocation #1365：DeepSeek V4 Pro，finish_reason `stop`，输入 7215、
  输出 5203，模型返回 `evt-17` 至 `evt-24`。
- focused collect：9 tests collected。
- focused pytest：9 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：
  401 passed, 1 skipped。
- 精确 isort/black：passed。
- repo docs/contracts diff 与 `git diff --check`：passed。
- `./docker/build_prod_images.sh`：passed（dirty build tag `6b1c35c3`）；
  backend manifest `15d3c611c890d0919bace5f72bd4d6c5df38987a85fbbd769b1a5010f8539533`，
  frontend manifest `c1a24193be05dff3c48cb3376374c5e2e9f72a6a5ed9b5c40471c1bbdec50871`。

## Next Steps

- 构建生产镜像、精确提交并加载 backend/worker。
- 仅 Resume Revision `50c17e...` 一次，确认第三批及后续批次逐事件覆盖。
- 规划全部通过后进入正文；达到两章再执行正式 cancel/hash snapshot/Resume。

## Linked Commits

- Pending
