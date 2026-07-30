## User Prompt

检查所有的提示词，确保小说生成提示词不与农业、种田、穿越或关系题材硬绑定，并继续通过真实链路生成。

## Goals

- 审计 v3 规划、正文、审计、返修、连续性及 Narrative Memory 提示词边界。
- 保证正文仅接收当前章人物、关系、事件、可见 Canon 与 brief，不接收原始 Event/Memory 或未来目录。
- 让章前 package 同时接收冻结题材元数据与小说版本的交付规格。

## Changes

- 将 `story_invariants` 和冻结 `novel_delivery` 长度规格加入逐章 package 输入。
- 将 `commercial_serial` 的商业连载节奏约束放在格式条件下，不绑定具体题材。
- 将 chapter package Prompt 版本升级至 `1.3`。
- 扩大题材中立回归扫描，覆盖 Story Novel、StorySeed 与 Narrative Memory 的动态 Prompt 源文件。
- 修正局部返修的长度方向判断：合并正文不足下限时扩写既有 replacement，超过上限时才压缩；扩写仍禁止新增关系、知识、权限、所有权、跨章线索或未来事件。
- 当前章角色焦点可解析到 Canon 的名称/别名实体，避免在 Prompt 缺少“家人”等合法实体时用无关可见角色代替。
- 非长度返修重试只携带待修改 replacements、精确错误、当前合同和只读邻块；重复段落必须从可编辑块删除并在当前场景内补足长度。
- 局部返修 Prompt 明确把 expand/compress/repair rewrite mode 放在最高优先级，并要求返回前按非空白字符自检，禁止超限后原样返回。
- 独立只读审查提出的 typed 状态泄露与全题材商业网文绑定已按当前代码复核：正文使用 prose-safe Canon projection，不含 from/to、knowledge proof、milestone/thread ID；商业节奏仅在冻结 story_format/target_audience 明确为连载或商业网文时启用。
- 将章前模型常见的 action phase 同义输出 `activity`/`reaction` 确定性归一为 `progress`/`instant`，避免把唯一一次格式修复浪费在传输枚举上；章前 Prompt v1.4 明确同一 subject/field 的每一条 typed effect 都必须逐事件认领，validator 仍拒绝任何漏绑。
- 完成第二轮全提示词审计，将 brief、chapter package 与 prose 中残留的固定“发现—判断—行动—结果”流程改为条件式题材中立表达；只有当前合同确实涉及观察、推理、专业能力或背景知识时才允许自然呈现，不得给无关题材强套流程。
- Prompt 版本更新为 chapter brief `1.3`、chapter package `1.5`、prose blocks `1.3`；扩大自动扫描词表，并把通用 StorySeed Prompt 纳入审计。
- 明确兼容边界：旧 v1/v2 动态正文及 Narrative 抽取 Prompt 仍有逐字日期/quote 合同，但 v3 provider 路径在调用前拒绝 unmanaged prompt 与 legacy fallback，当前质量保证不使用兼容 Prompt。
- 独立只读复核后修复 Prompt 内部 P1：允许合理自然时间推进；列全 `instant/start/progress/complete`；错误诊断补齐 `effect_coverage`；章节包格式返修从 4K 恢复到完整 12K。
- 审计用未来状态边界不再携带未来 `key_events` 原文；未来边界问题必须落入 `future_hits` 并绑定 `claim_id`，局部返修不会收到未来消息。
- 系统角色改为按阶段履责的叙事创作助手；正文只执行冻结 brief 的节奏，不再重复套商业公式。
- v26 真实 package 暴露派生位置适配缺口：非法 `field=location` 状态会被删除，但 stale-ref 校验误用了删除后的合同。现保留删除前模型合同仅用于 stale-ref 对照，不恢复非法状态；Prompt v1.7 明确 owner_id 派生的物件位置和人物 possessions 不得另造 typed effect。
- v27 继续暴露模型手抄 effect 编号的不稳定性：初稿重复认领，返修又漏掉同一 milestone 的 owner/state outcomes。Prompt v1.8 将 milestone outcomes 定义为原子组；服务端仅在至少一项 outcome 已有唯一事件归属时补齐同组引用，并补齐相同 subject/field/outcome 的 state alias。无可信归属或多事件歧义继续拒绝。

## Validation

- 27 个 `story_novel_*.txt` 模板与 27 个 YAML manifest 一一对应，无缺失或孤立 manifest；其中 20 个属于 v3，7 个属于 legacy Zhihu 兼容路径。
- 最终 Prompt/上下文/运行边界 focused：46 passed。
- 完整 Story Novel 单测：790 passed, 1 skipped, 653 warnings。
- black、isort、repo contracts diff、git diff --check：passed。
- 真实 v22 invocation 证明正文 Prompt 含当前人物、动机、事件和可见 Canon，原始 Event/Memory 与未来章节计数均为 0。
- v22 的 GPT-5.6 章内审计因 `server_is_overloaded` 失败；保留失败正文与调用审计，未提升 checkpoint。
- 全新 v23 Revision `9491b9995e9a455e91dcdc7d384e9204`、Task `6847` 真实生成第 1–2 章为 ready；第 3 章审计正确拒绝新增亲属/同住关系，但旧返修重试错误要求继续压缩，任务 fail-closed、未污染有效状态。
- v24 Revision `d7e8e825c8fe4e4ca2a210b9e47a6592`、Task `6850` 使用 DeepSeek Flash 正文模型：第 1 章首稿 1831 字；局部返修扩写后超过上限，格式返修已收到明确 compress 诊断但逐字返回同一 replacements，最终 fail-closed。invocation `#2874–#2880` 均完整审计，失败章保持 `review_required`，没有进入 ready checkpoint。
- v25 首次 Task `6851` 在正文前 fail-closed：`#2883` 把 action phase 写成 `activity/reaction`，`#2884` 修复枚举后仍漏绑第二段人物移动 `location:2`；0 章、无正文调用。该证据直接驱动上述枚举归一和多段 effect Prompt 补强。
- v26 Revision `1673563f0bb54f4bb6e216dab39e8cad`、Task `6852` 冻结实际 Prompt policy v5；Canon `#2885` 成功，package `#2886/#2887` 因 owner 派生位置被错误表示为 `state:1` 而在正文前 fail-closed。修复后 focused `20 passed`，完整 Story Novel `792 passed, 1 skipped`，格式与 contracts 全绿。
- v27 Revision `449723763ba443a08220253c7441c881`、Task `6853` 冻结 package Prompt v1.7；Canon `#2888` 成功，package `#2889/#2890` 因原子 milestone outcomes 漏绑而在正文前 fail-closed、0章。确定性原子组绑定后 focused `22 passed`，完整 Story Novel `794 passed, 1 skipped`，格式与 contracts 全绿。

## Next Steps

- 重启加载 Prompt v1.8 后新建干净 Revision，规划继续使用 DeepSeek Pro，正文与审计继续使用 Codex GPT-5.4；不得 Resume 已冻结旧策略的 v26/v27。
- 新 Revision 至少两章 ready 后完成正式 cancel/resume 与 hash 不变证明。
- 继续至 48/48，运行连续性、GPT-5.6 分批/全局审读、Word 导出与审批隔离验证；v23/v24 均只保留为失败证据，不计入本轮最终验收。

## Linked Commits

- Pending.
