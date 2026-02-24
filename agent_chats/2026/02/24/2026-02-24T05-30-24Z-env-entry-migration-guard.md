---
id: 2026-02-24T05-30-24Z-env-entry-migration-guard
date: 2026-02-24T05:30:24Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [engineering, docker, migrations, docs]
related_paths:
  - .gitignore
  - README.md
  - tasks.md
  - docker/README.md
  - docker/.env.prod.example
  - docker/init_env.sh
  - docker/migration_guard.sh
  - docker/dev_in_docker.sh
  - docker/dev_lite_in_docker.sh
  - docker/docker-compose.dev.yml
  - docker/docker-compose.prod.yml
summary: "补齐 dev/prod 统一配置入口与迁移未同步诊断/修复脚本，并更新任务看板与文档"
---

## User Prompt

继续

## Goals

1. 完成 P0 工程化项：统一配置入口与 dev/prod 样例。
2. 提供“迁移未同步”自动诊断与一键修复脚本。
3. 更新 README / docker 文档与 `tasks.md` 状态。

## Changes

1. 统一配置入口与样例

- 新增 `docker/.env.prod.example` 作为生产栈环境模板。
- 新增 `docker/init_env.sh`，统一初始化 env 文件：
  - `./init_env.sh dev` -> `.env.example` 到 `.env`
  - `./init_env.sh prod` -> `.env.prod.example` 到 `.env`
  - `./init_env.sh lite` -> `.env.lite.example` 到 `.env.lite`
- 支持 `--force` 覆盖、`--dry-run` 预览。
- `.gitignore` 新增 `!docker/.env.prod.example` 例外，确保模板纳入版本控制。

2. 迁移未同步诊断与一键修复

- 新增 `docker/migration_guard.sh`：
  - `check`：读取 `migration_manager.check_migration_status()` 自动诊断迁移是否同步。
  - `fix`：执行 `alembic upgrade head` 一键修复并自动复检。
  - 支持 `dev|prod`，并提供 `--dry-run`。
- 该脚本通过 docker compose 对 `ai-video-backend` 执行检查/修复，无需手工进入容器。

3. 文档与脚本提示更新

- `README.md`：
  - 快速开始改为 `./init_env.sh dev/lite`。
  - 新增配置入口说明（dev/prod/lite）。
  - 新增迁移诊断/修复命令（含 dry-run）。
- `docker/README.md`：新增统一 env 入口和 migration guard 使用说明。
- `docker/dev_in_docker.sh`、`docker/dev_lite_in_docker.sh`：缺少 env 时提示改为 `./init_env.sh ...`。
- `docker/docker-compose.dev.yml`、`docker/docker-compose.prod.yml`：移除过时 `version` 字段，避免 compose 警告。
- `tasks.md`：将“统一配置入口与样例（dev/prod）+ 迁移未同步诊断修复脚本”标记完成。

## Validation

1. 代码与格式

- `bash -n docker/init_env.sh docker/migration_guard.sh docker/dev_in_docker.sh docker/dev_lite_in_docker.sh`
- `pre-commit run --files .gitignore README.md docker/README.md docker/dev_in_docker.sh docker/dev_lite_in_docker.sh docker/docker-compose.dev.yml docker/docker-compose.prod.yml docker/.env.prod.example docker/init_env.sh docker/migration_guard.sh tasks.md`

2. 脚本行为验证

- `cd docker && ./init_env.sh dev --dry-run && ./init_env.sh prod --dry-run && ./init_env.sh lite --dry-run`
- `cd docker && ./migration_guard.sh check dev`（返回未同步时 exit code 2）
- `cd docker && ./migration_guard.sh check prod`（返回未同步时 exit code 2）
- `cd docker && ./migration_guard.sh fix dev --dry-run`

3. 强制构建门禁

- `./docker/build_prod_images.sh` 成功（backend/frontend 构建并推送，tag=`497aef8`）。

4. Chrome E2E（MCP）

- 路径：`/login` 登录 `geyunfei / Gyf@845261` -> 首页（显示“欢迎, geyunfei”）-> `/stories`（显示“故事管理”）。

## Next Steps

1. 若需要，可在 `migration_guard.sh` 增加 `lite` 栈专用策略（SQLite fallback 语义）。
2. 将 `migration_guard.sh check` 集成到 CI 或启动前检查脚本，减少运行时“Unknown column”风险。

## Linked Commits

- pending (this commit)
