## User Prompt

继续通过系统正式 API、真实 MySQL 和付费模型完成全新 48 章小说，
验证 Canon、状态链、未来剧情隔离、事实与记忆抽取、连续性、取消恢复和
GPT-5.6 全书审读。

## Goals

- 保持确定性 Canon/章节计划 validator 严格，不靠放宽门禁通过真实生成。
- 消除完整结构化大纲已在早期章节建立物件地点、模型却把同一地点写成未来
  一次性里程碑结果所形成的不可执行 Canon。
- 让缺少当前模型过滤版本的旧 Canon checkpoint 在 Resume 时重新编译。

## Changes

- 新增 Canon 模型输出过滤器：只有冻结结构化大纲在里程碑之前的同一章节
  同时明确提及 Canon 物件与地点时，才删除该物件重复的未来地点 outcome。
- 保留同一里程碑的其他状态结果，且不修改严格的 raw Canon normalize 和
  generation-plan validator。
- 在 Canon checkpoint 和最终计划记录过滤版本；旧版本或缺失版本不再被
  当作可直接复用的 v2 计划。
- 增加模型解析、无同章来源保留、旧 checkpoint 强制重编译及现有 Resume
  复用语义回归。

## Validation

- `pytest -q --no-cov tests/unit/test_story_novel_canon_milestone_filter.py tests/unit/test_story_novel_planning_repair.py tests/unit/test_story_novel_planning_resume.py`
  - 15 passed。
- `pytest -q --no-cov tests/unit/test_story_novel_*.py`
  - 366 passed, 1 skipped。
- `pre-commit run isort --files <7 changed Python paths>`
  - 首次机械调整导入顺序；提交前复跑。
- `pre-commit run black --files <7 changed Python paths>`
  - 首次机械格式化一个文件；提交前复跑。
- `python scripts/check_repo_contracts.py --mode diff <7 changed Python paths>`
  - ok。
- `python scripts/check_repo_docs.py`
  - ok。
- `git diff --check`
  - clean。
- `pre-commit run --all-files`
  - 全仓既有 ruff/格式基线失败；自动修复 hook 改动了大量本任务外文件，
    backend quick hook 尚未结束时已人工中止。本提交仅包含上列小说质量路径，
    不吸收这些无关机械改动。

## Next Steps

- 重启挂载当前提交的 backend/worker。
- 只对本轮 Revision 走一次正式 Resume，确认新 Canon 过滤诊断和分批 48 章
  规划，再继续正文、取消恢复与 GPT-5.6 验收。

## Linked Commits

- Pending
