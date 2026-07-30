## User Prompt

将长篇小说链路改为章前规划驱动，面向情节和吸引力优先的商业网文，默认每章
2000–3000 非空白字符，保留人物介绍、当前关系和当章事件，但不泄露未来剧情。

## Goals

- 减少 2000–3000 字章节的过度分块和内容重复。
- 让 Event/Memory 只用于章前规划，正文仅读取当前章安全投影。
- 保留 Canon/state/future/proof 的确定性硬门禁，将爽点、节奏、关系和钩子作为
  非阻断编辑信号。

## Changes

- 新增带版本的 brief policy：新计划每章 4–6 个大 beat，历史 checkpoint 继续使用
  6–12 个 beat。
- 新增商业网文长度 profile：2000 / 2500 / 3000。
- 正文 prompt 引入经过滤的当前章事件、当前可见人物介绍、动机、状态和关系，
  不引入原始 Event/Memory 或未来人物/关系。
- 更新章前规划、正文 block、Canon 和连续性模板，强化商业网文的冲突、可见得失、
  已授权人物关系推进和章末钩子，同时不强制关系升级或新增未规划设定。
- 全量审计当前 V3 真实运行模板，清除农业、穿越、男女主、特定交通/场所和工程
  例子；特殊设定与关系弧只能来自 StorySeed/Canon/当前章合同。
- 新增运行模板题材中性回归，防止特定题材词重新进入 V3 PromptManager 源文本。
- 六章连续性窗口增加读者留存警告，不作为确定性审批门禁。
- 真实 v21 首章规划暴露 state/milestone 重复表示与 knowledge source effect 漏绑定；
  服务端仅对同结果别名和已有 `source_event_id` 的 effect 做确定性补绑定，错事件、
  不同结果和未认领 effect 仍 fail-closed。

## Validation

- Backend prompt/contract focused: 33 passed.
- Hard-context/incremental regressions: 4 passed.
- Full Story Novel unit suite: 774 passed, 1 skipped.
- StorySeed thread contract and repair: 16 passed.
- Frontend commercial-length focused: 3 passed.
- Frontend lint: 0 errors, 3 unrelated existing warnings.
- Frontend full test baseline: 482 passed, 10 unrelated ProductionCanvas failures.
- Changed-code black/isort and repository contracts: passed before documentation sync.
- Prompt neutrality scans all `story_novel_*.txt` templates plus dynamic prompt
  modules; audited topic-specific terms have zero runtime prompt hits.
- Effect-coverage focused/incremental regressions: 24 passed; changed files black,
  isort, repository contracts and diff check passed.
- Real UI/MySQL run v21: Task 6827 failed at chapter-planning effect coverage with
  0 chapters; Task 6828 reproduced a source-bound knowledge ref omission after one
  legal format repair, also failed with 0 chapters. Both runs are preserved as
  fail-closed evidence; no chapter or candidate checkpoint was promoted.

## Next Steps

- 重跑文档与最终变更范围契约、backend quick、frontend build 和生产镜像。
- 通过 Docker dev Compose 与正式 UI/API/MySQL 生成一部新的 48 章穿越种田文，完成
  cancel/Resume hash 验证、GPT-5.6 八批加全书审读及正式审批。

## Linked Commits

- Pending.
