## User Prompt

用户确认长篇网文的成长应作为全书可选曲线，并要求人物与世界在剧情需要时依次扩展，而不是固定在初始人物和新手村；随后要求继续真实生成与质量闭环。

## Goals

- 保持认知、能力、资源、活动/时间尺度为全书规划与吸引力评审维度，不做逐章数值 KPI。
- 确保当前章已经授权的新人物、地点、组织或物件真正以名称或合法别名进入正文。
- 不向正文泄露未来章节，也不放宽状态、知识、未来事件或世界规则门禁。

## Changes

- 在 v3 正文确定性门禁中校验当前章 `entity_introductions` 的名称或别名是否真实出现。
- 将缺失实体绑定到其 brief beat，局部修复只改相关 block。
- 将当前章实体 ID、允许名称与 block ID 作为结构化安全修复约束；继续过滤审计模型自由文本和未来信息。
- 增加缺失具名人物、合法别名和安全修复输入回归测试。

## Validation

- 聚焦纯单元：`9 passed`。
- 完整 Story Novel 隔离运行：`842 passed, 1 skipped`；唯一失败为测试从临时 cwd 读取相对 Prompt 文件。
- 上述 cwd 依赖节点从仓库根目录单独复核：`1 passed`；合计业务结果为 `843 passed, 1 skipped`。
- 首次完整回归误重叠两份 pytest，导致共享 `test.db` 的 I/O/只读错误；该结果作废，随后改用独立临时目录串行复核。
- 真实 Revision 67 在第 20 章连续两次证明原问题：chapter brief 与可见 Canon 均包含周谨，但正文只写未具名男子，局部压缩也因未收到当前章姓名而无法修复；所有失败均 fail-closed，前 19 章保持 ready。

## Next Steps

- 重载 backend/worker 后，只从 Revision 67 第 20 章正式 Resume。
- 继续完成 48/48、连续性、GPT-5.6 分批与全书审读、DOCX、审批和 Canonical 提升。

## Linked Commits

- This commit: `fix(story): require named chapter introductions`
