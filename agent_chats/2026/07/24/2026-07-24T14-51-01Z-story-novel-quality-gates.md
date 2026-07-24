---
id: 2026-07-24T14-51-01Z-story-novel-quality-gates
date: "2026-07-24T14:51:01Z"
participants: [user, codex]
models: [gpt-5.6-sol]
tags: [backend, story-novel, canon, quality-gates, code-review]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_future_claims.py
  - ai-pic-backend/app/services/story/story_novel_canon_service.py
  - ai-pic-backend/app/services/story/story_novel_chapter_v2.py
  - ai-pic-backend/app/services/story/story_novel_continuity_service.py
  - ai-pic-backend/app/services/narrative_memory/candidate_service.py
summary: Close reviewed long-form quality gaps while freezing the selected planning and prose models.
---

## User Prompt

- AI 生成结构化章节时应支持输入章节数，并可选择结构化规划模型。
- 小说正文模型独立可选。
- 并行只读审查小说生成整体代码，由主任务判断并采纳有证据的修改意见。
- 最终仍需通过正式系统链路完成 48 章、取消/恢复、连续性检查与 GPT-5.6 验收。

## Goals

- 冻结结构化规划实际使用的模型，避免默认模型在队列执行时漂移。
- 保持规划模型与正文模型独立，并阻止已有正文后静默换模。
- 关闭未来事件审计、Canon 来源、Resume、Narrative Memory、连续性覆盖等审查发现的质量门禁缺口。
- 保持所有失败路径 fail closed，不放宽正确的状态或未来剧情门禁。

## Changes

- 要求逐章状态抽取完整审计全部未来事件 ID，并校验审计结果与提前兑现声明一致。
- 结构化规划任务入队时解析并保存实际 provider/model；规划结果保存正文模型，已有章节后禁止切换正文模型。
- Canon 世界规则只取自 StorySeed 静态世界约束，过滤章节化未来信息；世界规则例外不再跳过整条规则检查。
- ready 章节的 Resume hash 不一致时返回冲突并保留正文，禁止静默重写。
- 小说章节 Narrative Memory 候选只允许随整部小说审批提升，禁止逐条提前批准。
- 校验知识授予目标必须是 Canon 角色；连续性审读窗口在六章边界重叠，原始阻断文本统一提升为结构化阻断项。
- 强化结构化大纲伏笔契约：伏笔只在首次开启章声明，后续章节不得重复携带同一 ID。

## Validation

- `pytest -q --no-cov tests/unit/test_story_novel_*.py tests/unit/test_story_seed_*.py tests/unit/services/test_narrative_memory_*.py`
  - `439 passed, 1 skipped, 491 warnings`
- `pre-commit run black --files <32 exact quality paths>`: passed
- `pre-commit run isort --files <32 exact quality paths>`: passed
- `pre-commit run ruff --files <32 exact quality paths>`: passed
- `python scripts/check_repo_contracts.py --mode diff <32 exact quality paths>`: passed
- `python scripts/check_repo_docs.py`: passed
- `git diff --check`: passed
- `./docker/build_prod_images.sh`: passed for backend and frontend multi-arch images.
- `pre-commit run --all-files`: repository-wide historical formatting debt caused
  unrelated ruff/black/isort/prettier changes; the run was stopped before the
  backend gate and every unrelated tool edit was restored. Exact changed-path
  hooks above remain green.
- 真实 UI 首轮结构化规划证据：
  - Story `8eaacf5906fa4442a9b47eab74f85b10`
  - Task `6615` / `c85fd0e9d8e4443f9aa096e1ef1ded0b`
  - DeepSeek `deepseek-v4-pro`
  - invocation `#1242`、`#1243`
  - `max_tokens=33600`，证明未受 8192 限制
  - 旧 Prompt 对重复伏笔 ID 说明不足，任务正确 fail closed，正文为 0 章；本提交已收紧 Prompt，待重启后由正式 UI 重试。

## Next Steps

- 精确提交本质量门禁切片并重启挂载源码的 backend/worker。
- 通过现有登录 Chrome 更新静态世界约束并重新生成 48 章结构化计划。
- 创建 Revision，开始真实长篇生成；至少两章后正式取消并 Resume，验证已完成章 hash 不变。
- 完成 48/48 门禁、连续性检查、GPT-5.6 分批与全局审读、审批和运行 artifacts。

## Linked Commits

- Pending: `fix(story): close novel quality gate gaps`
