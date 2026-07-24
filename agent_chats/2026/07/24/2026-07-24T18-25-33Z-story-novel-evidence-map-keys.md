## User Prompt

继续通过系统正式 API、真实 MySQL 和付费模型生成全新 48 章小说；每章必须通过 Canon、状态、未来剧情、逐字证据和 Narrative Memory 门禁，并完成一次正式 cancel/Resume 后的 hash 不变验证。

## Goals

- 修复真实 Task 6627 第 3 章状态提取在空 immutable timeline 下返回额外 `timeline_evidence` key 后无法 extraction-only Resume 的问题。
- 只允许修复证据 map，不允许证据返修改写 typed state、正文或放宽未来剧情门禁。
- 保持第 3 章已 checkpoint 正文，并让后续正式 Resume 只重跑状态提取。

## Changes

- 删除证据返修前的 key 集合匹配短路，让缺失或额外 evidence-map key 也能进入有界 evidence-only repair。
- 在状态提取与证据返修 Prompt 中明确：两个 evidence map 的 key 必须严格等于冻结 ID 集合；空 immutable timeline 必须返回空对象。
- 增加额外 timeline ID 被删除且 typed state 保持不变的回归；原位置字段 typed-state 合同测试机械拆分到独立测试文件。

## Validation

- `pre-commit run isort --files <5 exact paths>` -> 首次机械修正 3 个文件；复跑通过。
- `pre-commit run black --files <5 exact paths>` -> 通过。
- `cd ai-pic-backend && pytest -q --no-cov tests/unit/test_story_novel_state_evidence_patch.py tests/unit/test_story_novel_state_evidence_key_repair.py tests/unit/test_story_novel_state_evidence_failures.py tests/unit/test_story_novel_state_extraction_repair.py` -> 9 passed，44 warnings。
- `cd ai-pic-backend && pytest -qq --no-cov --junitxml=/tmp/story-novel-quality-junit.xml tests/unit/test_story_novel_*.py tests/unit/services/test_narrative_memory_*.py` -> 433 collected，432 passed，1 skipped，0 failures/errors。
- 真实失败证据：Task 6627；第 3 章正文 hash `70b59f169d61e303e85add20551f611a741c7b44e6038e1975831fbb5eb28527`；state invocation #1310；repair invocation #1311。当前章节保持 `state_pending`，未应用错误状态。

## Next Steps

- 完成仓库 contracts、镜像构建和精确提交。
- 重启正式 backend/worker 后仅对 Revision `1fe57d4e72dd45f19281c3c524c2fbce` 调用一次 Resume API。
- 核验第 1–3 章正文 hash 不变，第 3 章只重跑状态与 Narrative Memory 提取。

## Linked Commits

- `fix(story): repair evidence map keys`
