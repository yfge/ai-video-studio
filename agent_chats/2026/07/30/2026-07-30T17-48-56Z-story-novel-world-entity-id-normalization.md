## User Prompt

用户确认认知、能力、资源、活动/时间尺度作为全书规划与终审的可选成长曲线，不作为逐章数值 KPI，并要求继续完成真实 48 章生成验收。

## Goals

- 通过正式 UI/API 和真实 MySQL 运行新的 48 章 Story Novel V3 链路。
- 保持人物与世界按剧情依次扩展，同时不放宽世界顺序、状态或未来剧情门禁。
- 修复真实运行中阻断第 1 章章前规划的稳定实体 ID 归一化错误。

## Changes

- `story_novel_world_expansion.py` 不再把新实体的展示名称加入临时引用替换表；只把模型声明的 `ref` 替换为服务端稳定 ID，避免实体自身 `name` 被误写成 ID。
- `test_story_novel_world_expansion.py` 增加名称、引入理由和完整世界扩展顺序校验，证明稳定 ID 与可读名称同时保留。

## Validation

1. Real runtime evidence:

- Story `e528ccc5d2884d6582d6ea2db9e61729`, Revision `37a9fc7a35e048f8b95a42edaf59001b`, Task `#6873`.
- Canon/planning invocation `#3099` succeeded (`8573` input, `6925` output, `finish_reason=stop`).
- Chapter planning invocation `#3100` succeeded, but deterministic validation rejected `char-local-1-bb4e6a81e8db`; format-repair invocations `#3101/#3102` then failed with `server_is_overloaded`.
- MySQL chapter count remained zero, so no body, candidate memory, or continuity state was promoted.

2. Local checks:

- `docker exec ai-video-backend ... pytest -o addopts= tests/unit/test_story_novel_world_expansion.py -q` -> `3 passed`.
- Full `tests/unit/test_story_novel_*.py` under the container's native FastAPI showed the known exception-string portability failures: `790 passed, 48 failed, 1 skipped`; failures match on an empty `HTTPException.__str__`, not product behavior.
- The same full suite with a test-process-only `HTTPException.__str__ = detail` compatibility shim -> `838 passed, 1 skipped`.
- Exact-file `pre-commit` isort and black -> passed.
- `python scripts/check_repo_contracts.py --mode diff ...` -> passed.
- `git diff --check -- ...` -> passed.

## Next Steps

- Restart the Celery worker so it loads the fix, then use the public Resume endpoint exactly once for Revision `37a9fc7a35e048f8b95a42edaf59001b`.
- After at least two ready chapters, cancel through the product, record persisted hashes, and Resume to 48/48 before continuity and GPT-5.6 review.

## Linked Commits

- This commit: `fix(story): preserve world entity names during ID binding`.
