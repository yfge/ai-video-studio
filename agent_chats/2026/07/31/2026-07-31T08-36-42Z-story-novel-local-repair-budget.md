## User Prompt

用户要求继续真实生成，并明确网文质量门禁不能把正文逼成严肃文学或审计报告；生成失败时应定位算法问题而不是盲目重试。

## Goals

- 修复局部长度返修中的矛盾模型目标。
- 保留章节 2,000–3,000 非空白字符硬门禁和有界两次返修。
- 用真实失败样本回归替换块预算，不做确定性截断或门禁放宽。

## Changes

- `replacement_length_contract` 的 `repair_model_target_chars` 改为所有可编辑 replacement 的总目标，不再错误复用全章目标。
- 全章 `chapter_target_chars` 仍独立保存并用于最终组装验收。
- 新增与真实第 10 章相同的 1,469 fixed + 1,031 replacement 预算回归。

## Validation

- 真实 Task `#6898` 第 10 章首稿 1,602 字符；返修合同同时给出 replacement 1,031 与 model 2,500，模型两次返回 2,345/1,776 字符 replacement，均无法与 fixed blocks 组合到 2,000–3,000，任务正确 fail-closed，11 章未生成。
- `cd ai-pic-backend && pytest -q tests/unit/test_story_novel_v3_length_repair_budget.py tests/unit/test_story_novel_v3_length_repair_selection.py tests/unit/test_story_novel_v3_repair_prompt_retry.py tests/unit/test_story_novel_v3_repair_retry.py tests/unit/test_story_novel_v3_combined_repair.py --no-cov` -> 24 passed。
- `cd ai-pic-backend && pytest tests/unit/test_story_novel_*.py -q --no-cov` -> 867 passed, 1 skipped。
- 精确 black/isort、repo contracts diff 和 `git diff --check` -> passed。

## Next Steps

- 重启 Worker，从第 10 章 Resume，验证 replacement 实际落入 824–1,237 字符并完成全章组装。
- 继续完成 48/48、连续性检查、GPT-5.6 评审、DOCX 和审批。

## Linked Commits

- This commit: `fix(story): target only editable repair blocks`
