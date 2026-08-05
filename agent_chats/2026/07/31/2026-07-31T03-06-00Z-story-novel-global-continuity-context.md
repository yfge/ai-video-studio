## User Prompt

继续改进长篇小说生成质量：人物、地点和世界范围应按故事需要逐步扩展；认知、能力、资源、活动/时间尺度是全书级软成长曲线，不得成为逐章 KPI。完成真实 48 章生成、连续性检查和 GPT-5.6 验收，并使架构可支撑约 200 万字的分卷长篇。

## Goals

- 修复真实 48 章全局连续性调用因 210 万字符重复上下文而超限的问题。
- 保留全部章节、Canon、状态链、Event/Memory 语义、来源 hash 和可核验证据。
- 将四条成长曲线作为全书编辑判断输入，不放宽逐章确定性门禁。
- 超预算时在 provider 调用前 fail closed，不静默裁剪章节或状态。

## Changes

- 新增 500,000 字符运输上限，并对最终渲染 Prompt 按冻结 audit model 做保守 token 估算；为 16K 输出和 16K 安全空间预留上下文。
- 只保留 generation plan 的 hash/version/model binding，不再重复整份计划和 StorySeed。
- 按来源章节分组全部世界事件与人物记忆，去除重复 source quote，完整保留候选 ID、source hash、typed 绑定和语义；缺失或重复 ID fail closed。
- 每章保留 body/source/context/state hash 链、typed state delta、世界实体引入、伏笔和摘要。
- 将原始 proof spans 压为 contract 到代表性 sentence ID 的导航映射，并保留去重后的原文 sentence index；窗口审读仍覆盖完整正文句索引。
- 全局抽样综合的新问题只可成为 warning；blocking 仍来自完整正文窗口或确定性硬指标，避免未展示句子产生虚假 grounding。

## Validation

- Focused continuity tests: `21 passed`.
- Full Story Novel unit suite after reviewer-driven hardening: `855 passed, 1 skipped`.
- Real MySQL Revision `e9f25fe3f74f45439f1fbaaf261ce58f`: 48 chapters, 146 events, 233 memories, 451 deduplicated global evidence sentences.
- With all eight persisted window reviews, the full-semantic payload is 464,859 characters and the rendered prompt is 467,031 characters / 211,081 conservative tokens, below the frozen Codex input budget of 240,000 tokens; the failed legacy global invocation used 2,101,121 prompt characters.
- An independent read-only reviewer raised three P1 findings around proof grounding, fixed character budgets and silent candidate clipping; all were adopted before runtime validation.
- No database write or provider call was used for payload measurement.

## Next Steps

- Restart the mounted backend and worker, then re-run continuity through the product UI/API.
- Complete GPT-5.6 eight-batch and global editorial review, DOCX export, approval isolation, and run artifacts.
- Record the high local block repair rate as a generation-reliability issue even if continuity passes.

## Linked Commits

- This commit: compact whole-novel continuity context.
