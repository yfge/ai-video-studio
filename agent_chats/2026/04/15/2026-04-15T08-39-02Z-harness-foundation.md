---
id: 2026-04-15T08-39-02Z-harness-foundation
date: "2026-04-15T08:39:02Z"
participants: [human, codex]
models: [gpt-5]
tags: [harness, docs, backend, frontend, refactor]
related_paths:
  - AGENTS.md
  - README.md
  - ARCHITECTURE.md
  - FRONTEND.md
  - RELIABILITY.md
  - SECURITY.md
  - QUALITY_SCORE.md
  - docs/README.md
  - docs/exec-plans/active/harness-foundation.md
  - docs/exec-plans/completed/README.md
  - docs/generated/db-schema.md
  - .pre-commit-config.yaml
  - .gitignore
  - .dockerignore
  - .github/workflows/ci-harness.yml
  - .github/workflows/nightly-harness.yml
  - scripts/check_repo_docs.py
  - scripts/check_repo_contracts.py
  - scripts/harness/bootstrap_worktree.sh
  - scripts/harness/_common.py
  - scripts/harness/scenarios.py
  - scripts/harness/doctor.py
  - scripts/harness/browser_flow.py
  - scripts/harness/run_golden_path.py
  - scripts/harness/trace_run.py
  - scripts/harness/trace_task.py
  - ai-pic-backend/app/core/config.py
  - ai-pic-backend/app/core/logging.py
  - ai-pic-backend/app/core/log_context.py
  - ai-pic-backend/app/core/json_logging.py
  - ai-pic-backend/app/main.py
  - ai-pic-backend/.dockerignore
  - ai-pic-backend/requirements-harness.txt
  - ai-pic-backend/requirements.txt
  - ai-pic-frontend/package.json
  - ai-pic-frontend/.dockerignore
  - ai-pic-frontend/src/hooks/useApi.ts
  - ai-pic-frontend/src/utils/api/client.ts
  - ai-pic-frontend/src/utils/api/trace.ts
  - ai-pic-frontend/src/utils/api/types/common.types.ts
  - docker/.env.lite.example
  - docker/README.md
  - docker/build_prod_images.sh
  - docker/docker-compose.lite.yml
  - docker/Dockerfile.backend.dev
  - docker/Dockerfile.frontend.dev
  - tests/harness/test_common.py
  - tests/harness/test_repo_contracts.py
summary: "Established the first harness-first repo foundation with doc/system-of-record split, repo gates, structured trace metadata, artifact-oriented bootstrap, and build-path fixes for lite stack throughput."
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN:

ai-video-studio Harness Engineering 整体落地方案

## Goals

- 将仓库从文档约束为主，推进到可执行的 harness-first 基础设施。
- 固化 worktree bootstrap、artifact 目录、repo doc drift / contract gates、前后端 trace contract。
- 为后续 browser evidence 和黄金链回归准备最小可用 CLI、CI 和质量面。

## Changes

- 新增 system-of-record 文档面：`ARCHITECTURE.md`、`FRONTEND.md`、`RELIABILITY.md`、`SECURITY.md`、`QUALITY_SCORE.md`、`docs/exec-plans/*`、`docs/generated/db-schema.md`，并把 `AGENTS.md` 收缩为入口与强制 gate。
- 新增 harness CLI 基础：`bootstrap_worktree.sh`、`doctor.py`、`browser_flow.py`、`run_golden_path.py`、`trace_run.py`、`trace_task.py`，统一落 `artifacts/runs/<run_id>/...`。
- 新增 `scripts/check_repo_docs.py` 与 `scripts/check_repo_contracts.py`，并接入 `.pre-commit-config.yaml` 与 `.github/workflows/ci-harness.yml` / `nightly-harness.yml`。
- 后端新增结构化 JSONL 日志与请求上下文透传：`run_id`、`request_id`、`task_id` 等字段进入日志与响应头。
- 前端 API 客户端与 hook 统一透传 `X-Harness-Run-ID` / `X-Client-Request-ID`，并把 trace 元数据回收到 `ApiResponse.trace`。
- 修复 lite stack 构建路径：dev compose 改为服务级 build context，新增前后端 `.dockerignore`，并为后端 dev Docker build 增加 harness constraints，消除 `langgraph` 解析回溯导致的 bootstrap 卡顿。
- 为提交前生产镜像 gate 补齐本地可运行路径：根 `.dockerignore` 排除大目录，`docker/build_prod_images.sh` 支持 `BUILD_PUSH=false` 时走 classic builder 本地构建，后端 `requirements.txt` 将 `langgraph` 固定为 `0.4.0` 以稳定 prod build 解析结果。
- 新增根级 harness 单元测试，覆盖 `_common` helper 与 repo contract 的关键规则。

## Validation

- `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/test_basic.py ai-pic-backend/tests/api/v1/test_diagnostic_endpoints.py -v`
  结果：`10 passed, 3 skipped`
- `ai-pic-backend/.venv/bin/python -m pytest tests/harness -v`
  结果：`5 passed`
- `ai-pic-frontend/npm run lint`
  结果：通过，仅现有 warning，无 error
- `ai-pic-frontend/npm run test`
  结果：`5 passed`
- `python3 scripts/check_repo_docs.py`
  结果：`[check_repo_docs] ok`
- `python3 scripts/check_repo_contracts.py ...`
  结果：通过
- `HARNESS_RUN_ID=local-harness-prepared scripts/harness/bootstrap_worktree.sh --mode lite --no-start`
  结果：生成 `artifacts/runs/local-harness-prepared/manifest.json`
- `DOCKER_BUILDKIT=0 docker build -t ai-video-studio-harness-frontend-test -f docker/Dockerfile.frontend.dev ai-pic-frontend`
  结果：build context 从仓库级缩到 `1.95MB`，镜像构建成功
- `DOCKER_BUILDKIT=0 docker build -t ai-video-studio-harness-backend-test2 -f docker/Dockerfile.backend.dev ai-pic-backend`
  结果：build context 为 `22.88MB`，并通过 `requirements-harness.txt` 将 `langgraph` 解析固定到 `0.4.0`，消除了长时间回溯
- `HARNESS_RUN_ID=local-harness-live DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 scripts/harness/bootstrap_worktree.sh --mode lite`
  结果：lite stack 成功启动，生成 `artifacts/runs/local-harness-live/manifest.json` 与 `bootstrap.log`
- `python3 scripts/harness/doctor.py --run-id local-harness-live --frontend-url http://localhost:3229 --api-url http://localhost:8229 --nginx-url http://localhost:9229`
  结果：`doctor: ok`
- `python3 scripts/harness/run_golden_path.py --scenario mock_smoke --run-id local-harness-live --api-url http://localhost:8229 --base-url http://localhost:9229`
  结果：`mock_smoke` 通过并写入 `golden_path.json`
- `python3 scripts/harness/browser_flow.py --scenario login_smoke --run-id local-harness-live --base-url http://localhost:9229`
  结果：artifact 已落 `browser_flow.json` / `console.json` / `network.json`，但当前环境下三层浏览器引擎都失败：
  Chrome DevTools MCP 无法从 CLI 进程附着，Playwright 缺少 `@playwright/test`，Selenium 无法创建本地 Chrome session
- `pre-commit run repo-doc-drift --all-files && pre-commit run repo-contracts --all-files && pre-commit run agent-chats-ledger --all-files`
  结果：全部通过

## Next Steps

- 在新 dev image 缓存可用后，补一次完整 `bootstrap_worktree.sh --mode lite`，再跑 `doctor.py`、`browser_flow.py --scenario login_smoke`、`run_golden_path.py --scenario mock_smoke`。
- 将 `QUALITY_SCORE.md` 从静态占位升级为由 nightly / golden path 自动回写。
- 按黄金链优先级，把 `timeline_export_regression` 从 timeline task 完成校验推进到 render/export 端到端断言。
- 继续把 choke point 拆分工作绑定到 repo contracts 和 browser scenario，而不是先做全仓大重构。

## Linked Commits

- Pending
