## User Prompt

启动付费小说生成。

## Goals

- 以主工作区当前 V5 链路新建约 100 万字、500 章、每章目标 2000 字的真实付费小说任务。
- 以任务、Revision、模型调用、Schema hash 和批次 checkpoint 证明真实运行边界。
- 若运行暴露 V5 阻断，只做题材无关的最小修复，并保留失败 Revision 作为证据。

## Changes

- 为 V5 Foundation、Causal Batch 和非批量 Schema 编译加入由通用一致性 Pydantic 契约生成的 provider-facing JSON Schema。
- 将结构化输出契约写入受管 prompt，并在模型调用层向 DeepSeek 请求 JSON object 输出；没有新增任何题材谓词或业务枚举。
- 将 condition/effect 的通用操作符、顶层字段、角色选择器与 required 字段写入 provider JSON Schema；非法 `add`、嵌套 `fact` 和缺失 `op` 不再是模糊对象。
- 因果批次的规划输入只投影 `causal` 谓词，避免模型把 observational 描写写入硬状态；冻结 Schema 本身保持完整。
- 修正取消保护包装器对 `json_schema` 的透传，并补充回归测试。
- 扩展 V5 invocation gate，使 500 章批量 Schema 编译按一个 Foundation 加 32 个因果批次核对调用证据。
- 改善纯一致性内核对缺失顶层 `predicate_id` 的错误信息，仍保持未知结构 fail-closed。
- 真实运行保留全部失败边界：Revision 78 为旧字段别名；Revision 79 为包装器未透传参数；Revision 80 为嵌套 `fact`；Revision 81 为非法/缺失 `op`；Revision 82 已冻结 Schema，但首批事件实体/角色绑定不闭合。

## Validation

- V5 聚焦测试：`28 passed, 1 skipped`。
- 变更文件 pre-commit（跳过已单独运行且存在仓库基线失败的 backend-pytest）：格式、Ruff、Black、isort、Prettier、文档和仓库契约均通过。
- 仓库 backend-pytest：`3365 passed, 65 skipped, 6 failed, 16 errors`；失败/错误位于既有渲染、记忆、任务持久化和 story parser 测试，不包含本次 V5 测试。
- 最终付费 Revision 82 / Task 6953 使用 `deepseek:deepseek-v4-pro`：Foundation 4372/4373 成功，Schema hash `73a116637fe160ebfaa877cae3516928510227c668897157b5fab02ef6a7bb24`，初始快照 hash `b60dc606f3178a8cebba2eb62b2fc22e3dafe8a6e74b3c559844ed98d7b81192`。
- 首批因果调用 4374 因 provider incomplete chunked read 失败后自动重试；4375 与唯一修复 4376 均获真实响应，但最终确定性诊断为 `event evt-ch01-001 role bindings are incomplete`。Task 6953 fail-closed，0 章、0 字、无状态补丁。
- 浏览器证据使用 Playwright fallback；Chrome DevTools 超时，不宣称 Chrome 验证。页面显示 Task 6953 failed、Schema/初始快照短 hash 和首批诊断；业务 API 均为 200，控制台仅 React DevTools/HMR 信息，初始导航有三个 `ERR_ABORTED` 请求。

## Next Steps

- 停止付费重试。下一设计点是题材无关的“事件期新实体”生命周期：当前因果批次只能绑定 `snapshot_before_batch` 已有实体，而 Foundation 又不展开逐章事件，无法可靠预声明每章产生的电话、证据或危机实例。
- 在补齐新实体声明/首用/生命周期及对应模拟规则前，不继续 500 章任务；补齐后先以 16 章因果批次 checkpoint 为门禁，再进入正文生成。
- 完成长篇后另行执行中断恢复、全量 hash 链、GPT-5.6 分批与全局复核，未完成前不宣称百万字验收完成。

## Linked Commits

- Pending in this commit.
