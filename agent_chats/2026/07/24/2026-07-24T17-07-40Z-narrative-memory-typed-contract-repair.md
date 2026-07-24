## User Prompt

继续通过正式系统链路生成并验收 48 章小说；每章必须完成事实、角色记忆、
typed state 和未来剧情门禁，失败时保留 checkpoint 并最小修复后继续。

## Goals

- Narrative Memory 模型输出必须精确覆盖 typed events 和 typed knowledge grants。
- 额外未绑定事件或记忆不得进入修订版内 Canon。
- 合同错误应使用已有的一次结构化修复机会，而不是在 provider 调用结束后才失败。

## Changes

- 新增 typed candidate `extra_validator`，在结构化输出阶段核对事件和记忆集合。
- events 必须与 `event_evidence` 一一对应，每条只有一个已知 typed event ID。
- memories 必须与 `required_memory_grants` 一一对应；无 grant 时必须为空。
- Prompt 明确禁止空、重复、未知、多 ID 事件以及未绑定普通印象。
- 新增端到端单元回归：首稿含额外 untyped 事件和记忆，修复稿只保留精确集合。
- 保留原有严格 candidate 构建、逐字证据、claim binding 与事务接口。

## Validation

- Task 6621 / Invocation #1296 真实证据：
  - #1296 使用 `deepseek-v4-pro`，3440 input、10521 output、`stop`，
    response hash `6e1f15918d87eb5f…`；
  - 模型正确覆盖 3 个 typed events，但额外返回 3 个空 typed ID 事件和
    5 个无 typed grant 记忆；
  - 系统 fail-closed，Task FAILED，0 个 Event/Memory 候选写入；
  - 第 1 章正文与 typed state checkpoint 保留。
- focused typed contract / claim / evidence tests：31 passed。
- Story Novel + Narrative Memory 完整单元集合：
  425 passed, 1 skipped。
- 四个精确路径的 isort、black、repo contracts、repo docs 与
  `git diff --check` 均通过；`extraction_service.py` 为 249 行。

## Next Steps

- 重启 backend/worker 加载本提交。
- 对 Revision `1fe57d4e72dd45f19281c3c524c2fbce` 正式 Resume 一次。
- 验证只重跑第 1 章 Narrative Memory，不改写其 body/content hash。
- 第 2 章完整 ready 后执行正式 cancel/hash snapshot/resume。

## Linked Commits

- Pending
