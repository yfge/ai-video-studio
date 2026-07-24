## User Prompt

继续完成 Canon 状态门禁与长篇小说质量闭环；章节生成必须携带既有 facts、角色记忆与情节，同时不得泄露未来剧情。结构化章节支持章节数和规划模型，正文支持独立生成模型。

## Goals

- 修复真实章节中 Narrative Memory 要求“事件证据”和“角色获知证据”为同一文本而形成的不可满足合同。
- 保持角色知情边界、来源逐字证据、future audit、typed state 与审批复核 fail closed。
- 让 Canon NPC 的状态知识保留在 ledger，同时只为真实 StoryCharacter 生成并强制覆盖 Character Memory。

## Changes

- 为 typed state delta 增加 `knowledge_evidence`，以稳定的 `character_id|fact_id|source_event_id` 绑定连续正文获知句。
- 新增共享的角色获知证据校验：正文逐字存在、明确角色归因、单一获知关系，并且是对应 event evidence 的完整片段。
- 章节正文、状态提取和证据返修 Prompt 均要求逐项写出和提取角色获知句。
- Narrative Memory 改为使用 grant 自己的 evidence，而不是强迫 memory evidence 等于整段事件 evidence；审批边界再次核对 typed grant 与 frozen quote。
- Narrative claim verification 升级到 v4，使旧的事件整段证据候选不能冒充新获知证据合同。
- 章节 checkpoint 保存 `memory_grant_keys`，严格覆盖可映射 StoryCharacter 的 grants，跳过没有持久化角色记录的 Canon NPC。

## Validation

- 定向知识证据与记忆候选测试：19 passed。
- 失败回归复核：16 passed。
- 完整 Story Novel + Narrative Memory 单测：472 passed, 1 skipped。
- 精确 isort：passed。
- 精确 black：passed。
- `python scripts/check_repo_contracts.py --mode diff <本切片>`：passed。
- `python scripts/check_repo_docs.py`：passed。
- `git diff --check`：passed。
- `./docker/build_prod_images.sh`：backend/frontend 双架构镜像构建并推送成功。
- 真实 UI/API 回归将在本提交后执行。

## Next Steps

- 完成 repo contracts 与生产镜像构建。
- 重启挂载当前代码的 backend/worker。
- 通过正式 UI 对当前质量验收 Revision 局部重生成第 1 章，验证 `knowledge_evidence`、候选记忆和 checkpoint。
- 达到至少两章后执行正式 cancel/hash snapshot/resume，再继续 48/48 与 GPT-5.6 审读。

## Linked Commits

- This commit: `fix(story): bind character knowledge evidence`
