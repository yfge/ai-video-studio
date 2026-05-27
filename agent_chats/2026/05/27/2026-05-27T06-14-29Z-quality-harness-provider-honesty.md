## User Prompt

继续推进 Timeline-first 内容质量验证，修复真实系统 API 回归中暴露的问题，保持诚实证据链。

## Goals

- 不把 Seedance 账号/额度问题误判成普通内容生成失败。
- 修正 production quality harness 的剧本质检路径，避免同步 linter 的 LLM cliffhanger 缺失造成假扣分。
- 把主角视觉锚点从 Timeline seed 带入 Timeline shot-plan，降低跨镜头角色漂移。
- 保持文件尺寸契约和测试证据可复查。

## Changes

- `provider_chain_api.request_json` 在 HTTP 4xx/5xx 时把响应正文写入异常 message，保留 provider 原始错误。
- `provider_chain_regression` 从异常和 request_chain response_body 中分类 `provider_billing_or_quota_failed`。
- `production_quality_api_checks.py` 拆出 live 质量回归的系统 API 剧本 lint 和 ScriptScore 调用。
- `production_quality_script.py` 增加异步 LLM cliffhanger lint；剧本正文场景头从 `# 第1场` 改为 `[第1场]`，匹配仓库 linter。
- `provider_chain_payloads.py` 收紧 DeepSeek 剧本提示：单主角、短对白、开场冲突、结尾未解决反转。
- `provider_chain_timeline_payloads.py` 在 Timeline seed `source_refs` 写入主角 name/appearance/anchor hint。
- `timeline_shot_plan_payloads.py` 在 shot-plan prompt 中要求复用同一个 protagonist anchor，并把 anchor hint 交给 DeepSeek。
- `provider_chain_media.py` 对 Seedance prompt 做 whitespace normalization，并记录 `prompt_source` 与原始 Timeline prompt。
- 增补 provider failure、prompt normalization、async script lint、Timeline anchor hint 测试。

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_failures.py tests/scripts/test_provider_chain_regression.py tests/scripts/test_provider_chain_media.py tests/scripts/test_production_quality_regression.py tests/test_timeline_shot_plan_api.py -q` -> pass, `22 passed`.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> pass.
- `git diff --check` -> pass.
- `cd ai-pic-backend && python run_tests.py quick` -> blocked before tests. Dependency install cannot resolve Python 3.13 constraints: `pydantic==2.5.0` conflicts with `langchain-core==0.2.43` requiring `pydantic>=2.7.4` on `python_full_version >= 3.12.4`.

2. System API probes:

- `seedance-billing-probe-20260527T-local` called `/api/v1/ai/generate/video` with an existing public character image and 4s Seedance 2.0 i2v request.
- Result artifact: `artifacts/runs/seedance-billing-probe-20260527T-local/provider_chain.json`.
- Result: failed honestly as `provider_billing_or_quota_failed`; response body includes Volcengine `AccountOverdueError` / overdue balance.
- `script-lint-probe-20260527T-local` evaluated existing sample-01 script through system API DeepSeek cliffhanger lint. Result: `status=completed`, `overall_score=8.5`, failed only `cliffhanger`.
- `quality-audit-after-harness-fix-20260527T-local` read existing sample-01 evidence. Result artifact: `artifacts/runs/quality-audit-after-harness-fix-20260527T-local/quality_report.json`; verdict remains `not_trial_ready`.

3. Browser or MCP validation:

- Not run for this commit. The change is backend/harness evidence classification and prompt/quality plumbing; no frontend route or UI behavior changed.

4. Conflict signals and corrections:

- Initial quality report labeled most Seedance failures as generic `seedance_generation_failed`.
- Backend logs contradicted that: Volcengine returned `AccountOverdueError` after sample-01 succeeded.
- The harness now preserves 400 response bodies and categorizes quota/billing failures explicitly.

## Next Steps

- Restore/fund the Volcengine Seedance account, then rerun `production_quality_regression.py --mode live-10`.
- After provider billing is fixed, reassess 10-sample success rate, script lint/ScriptScore, frame contact sheets, and rendered 30s outputs.
- If scripts still fail cliffhanger quality after billing is fixed, tighten DeepSeek premise/prompt or add an automatic rewrite loop before Timeline seed.

## Linked Commits

Pending
