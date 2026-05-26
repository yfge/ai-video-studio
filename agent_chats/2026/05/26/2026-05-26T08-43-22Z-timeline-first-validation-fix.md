## User Prompt

继续补齐 Timeline-First 全链路，按项目规范提交并验证。

## Goals

- 修复提交后 backend quick gate 暴露的生产链路单测失败。
- 保证生产 storyboard 单测不再真实调用 DeepSeek。
- 保留 Timeline shot plan 写回后版本递增的真实预期。

## Changes

- 更新 `tests/unit/services/script/test_production_storyboard_timeline_import.py`：
  - mock `TimelineShotPlanService.generate_shot_plan_for_timeline`，避免 unit test 真实调用外部 AI。
  - 将生产链路返回的 Timeline 版本断言从 `1` 调整为 shot plan 写回后的 `2`。
- 保留 pre-commit 产生的 import/formatting 调整。

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/script/test_production_storyboard_timeline_import.py::test_auto_timeline_placeholders_imports_timeline_spec_and_checks_audio -q`
  - Result: passed, `1 passed`.
- `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_regression.py tests/scripts/test_provider_chain_media.py tests/integration/test_timeline_pipeline_import_api.py tests/unit/services/script/test_production_storyboard_timeline_import.py::test_auto_timeline_placeholders_imports_timeline_spec_and_checks_audio -q`
  - Result: passed, `9 passed`.
- `pre-commit run --files $(git diff --name-only HEAD~3..HEAD) $(git diff --name-only) $(git ls-files --others --exclude-standard)`
  - Result: passed; backend quick gate passed in the active environment.
- `python scripts/check_repo_docs.py`
  - Result: passed.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only HEAD~3..HEAD) $(git diff --name-only) $(git ls-files --others --exclude-standard)`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- `cd ai-pic-backend && python run_tests.py quick`
  - Result: blocked during dependency installation before tests; Python 3.13 resolver conflict between pinned `pydantic==2.5.0` and `langchain-core==0.2.43` requiring `pydantic>=2.7.4` on Python 3.12.4+.
- `pre-commit run --files $(git diff --name-only HEAD~3..HEAD)`
  - Result before this fix: failed in backend quick gate on `test_auto_timeline_placeholders_imports_timeline_spec_and_checks_audio`; earlier hooks passed.

## Next Steps

- Re-run backend quick gate and repository checks after this fix.
- Run live provider-chain smoke if local API is reachable.

## Linked Commits

- Pending
