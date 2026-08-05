## User Prompt

用户质疑新版小说生成为何没有使用仓库已有的 PromptManager/模板机制，要求继续按
章前规划驱动的 V3 长篇链路改造，并最终用真实种田文生成验证。

## Goals

- 让结构化大纲、Canon、章节规划、章前 brief、正文、审计与有界返修使用统一模板系统。
- 保留 V3 的 typed contract、future isolation、严格 JSON 与 fail-closed 门禁。
- 冻结模板版本和 source hash，并把实际 rendered hash 绑定到 invocation/continuity 证据。
- 不复用旧知乎模板，不改变 legacy 知乎导出行为。

## Changes

- 新增 Story Novel V3 专用 `.txt/.yaml` 模板，覆盖 system、结构化大纲及两类修复、
  Canon、伏笔调度/修复、批次章节合同、语义审计、定点/完整计划修复、章前 brief、
  正文 blocks、截断续写、proof 审计、局部 block 返修、JSON 修复和连续性审读。
- 新增薄的小说模板 renderer，统一调用 PromptManager，并生成模板名、版本、模板 source
  hash 与本次 rendered hash。
- 新 V3 generation plan 冻结 `story_novel_prompt_policy.v2`；旧 v1 policy 只按其自身
  快照校验，避免用当前模板清单重算并误伤历史 Revision。
- 章节 stage invocation 把 user rendered hash 和 system template fingerprint 持久化到
  调用审计并写入 continuity ledger；`finish_reason=length` 的 rejected invocation 也
  完整绑定，V3 审批同时核对 ledger 与真实 invocation metadata。
- 保持原小说链路紧凑 JSON 字节格式，避免模板迁移放大 48 章 token 预算。

## Validation

- PromptManager、规划/修复、连续性、调用审计与审批 focused：81 passed。
- 完整 `tests/unit/test_story_novel_*.py`：592 passed, 1 skipped。
- 精确 Python 路径 black/isort：通过。
- `git diff --check`：通过；repo contracts 在最终文档更新后复跑。

## Next Steps

- 通过正式 Prompt API 和一次真实 V3 调用验证 policy v2、system/user 指纹与截断证据。
- 完成 backend/frontend/repo 验证并重启 Docker dev 链路。
- 使用正式 UI/API 和 MySQL 新建 V3 Revision，完成 48 章种田文、cancel/Resume/hash、
  GPT-5.6 分批及全书审读，再决定审批与 Canon 提升。

## Linked Commits

- Pending.
