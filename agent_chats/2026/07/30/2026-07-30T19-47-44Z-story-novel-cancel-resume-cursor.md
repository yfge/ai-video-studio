## User Prompt

真实 48 章验收必须在至少两章 ready 后通过正式产品入口取消，再 Resume 到结尾，并证明已有章节 business ID、正文和全部 hash 不被静默重写。

## Goals

- 取消发生在下一章 provider 调用中时，也能从持久化 ledger 确定首个未完成章节。
- 不依赖取消 API 与 worker 返回之间的竞态来保存 Resume cursor。
- Resume 前验证 ready 前缀并持久化推导出的 cursor，禁止回退到第 1 章。

## Changes

- 当 `stale_from_position` 尚未写入时，从 ledger 中第一个非 `ready` 章节确定性推导 Resume 起点。
- 对推导起点之前的章节继续执行完整 hash、状态链、proof 和 Narrative candidate 校验。
- 校验通过后写入 `state_status=stale` 与推导出的 cursor； fresh Revision 仍从第 1 章开始。
- 回归覆盖 context compiler 变化、缺失 cursor 的 ready 前缀和无效前缀 fail-closed。

## Validation

- 真实 Revision `e9f25fe3f74f45439f1fbaaf261ce58f`、Task `#6880` 生成两章后经正式 UI 取消，Task terminal 为 `CANCELLED`。
- 取消前快照：第 1 章 `3079fe5e58284bfb95d569cebb9bc336` / body `9493743e...` / 2966 字；第 2 章 `d37f31f766c84723aa204157fb9fe824` / body `e84014a9...` / 2818 字。
- 被取消的第 3 章 planning `#3217` 最终返回，但任务未接纳：数据库保持 2 个 ready 章节、0 个 review_required。
- Resume cursor 聚焦：4 passed；Resume/取消/并发/V3 审批集合：30 passed。
- 完整 Story Novel 单测（测试进程内适配既有 FastAPI 异常字符串差异）：840 passed、1 skipped。
- isort、black 通过。

## Next Steps

- 精确提交并重启 worker。
- 对当前 Revision 正式 Resume 一次，验证首个新 invocation 为 `chapter_planning.3` 且前两章全 hash 不变。
- 继续生成至 48/48，完成连续性、GPT-5.6 审读、DOCX 和审批。

## Linked Commits

- Pending
