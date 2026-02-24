---
id: 2026-02-24T04-55-16Z-lite-dev-mode-sqlite-eager
date: 2026-02-24T04:55:16Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [engineering, docker, backend, docs]
related_paths:
  - .gitignore
  - README.md
  - tasks.md
  - docker/README.md
  - docker/backend-entrypoint.sh
  - docker/docker-compose.lite.yml
  - docker/dev_lite_in_docker.sh
  - docker/.env.lite.example
  - ai-pic-backend/app/core/config.py
  - ai-pic-backend/app/core/celery_app.py
  - ai-pic-backend/app/services/ai/base.py
  - ai-pic-backend/env.example
summary: "新增 lite 开发模式并修复 SQLite 迁移/登录链路，补齐文档与任务看板"
---

## User Prompt
对比参考项目后，继续推进差距补齐；将进展更新到 `tasks.md`，并开始执行，持续“继续”直到可落地提交。

## Goals
1. 提供 5-10 分钟可启动的 lite 开发模式（SQLite + eager Celery + mock AI）。
2. 保留现有全量 Docker 开发栈，不破坏原流程。
3. 更新 README 与 docker 文档，并把对应任务标记完成。
4. 用真实运行和浏览器路径验证，不靠口头判断。

## Changes
1. 后端配置新增 lite 开关：
- `ai-pic-backend/app/core/config.py` 增加 `CELERY_TASK_ALWAYS_EAGER`、`CELERY_TASK_EAGER_PROPAGATES`、`AI_FORCE_MOCK`。
- `ai-pic-backend/app/core/celery_app.py` 统一 eager 判定逻辑（pytest/lite），并配置 eager propagate。
- `ai-pic-backend/app/services/ai/base.py` 支持 `AI_FORCE_MOCK=true` 时跳过 provider manager。
- `ai-pic-backend/env.example` 增加 lite 相关示例变量（含 `SQLITE_MIGRATION_FALLBACK_CREATE_ALL`）。

2. Docker lite 栈落地：
- 新增 `docker/docker-compose.lite.yml`（backend/frontend/nginx，移除 `version` 字段）。
- 新增 `docker/dev_lite_in_docker.sh`（构建并启动 lite 栈）。
- 新增 `docker/.env.lite.example`（SQLite + eager + mock 默认；`NEXT_PUBLIC_API_URL` 默认改为 `http://localhost:8089`）。
- 更新 `.gitignore`，放行 `docker/.env.lite.example`。

3. SQLite 迁移失败的可运行修复：
- `docker/backend-entrypoint.sh` 在 SQLite 下 Alembic 失败时，按 `SQLITE_MIGRATION_FALLBACK_CREATE_ALL` 回退：
  - 重置 sqlite 文件。
  - `create_all` 初始化 schema。
- 这是为 lite 快速启动兜底，避免 MySQL 风格迁移语句阻断启动。

4. 文档与看板：
- `README.md` 增加 lite 5-10 分钟启动路径，并保留完整 Docker 栈说明。
- `docker/README.md` 增加 Lite quick start、关键变量与默认 API 地址。
- `tasks.md` 将“工程化：lite 开发模式...”打勾完成。

## Validation
1. 自动化校验：
- `cd ai-pic-backend && pytest` -> `1883 passed, 87 skipped`。
- 定向 `pre-commit run --files ...` -> 全部通过。
- `./docker/build_prod_images.sh` -> backend/frontend 多架构镜像构建并推送成功。

2. Lite 栈运行验证：
- `docker compose --env-file .env.lite -f docker-compose.lite.yml up -d --build` 成功拉起。
- `curl -I http://localhost:8000/docs` -> `200`。
- `curl -I http://localhost:8089/login` -> `200`。

3. 冲突信号复盘（按“不要嘴硬”执行）：
- 先观察到 lite 后端因 SQLite 不支持 `ALTER COLUMN` 迁移失败。
- 修复后再次用真实请求验证，发现登录接口仍 `500`，日志显示 `users.business_id` 缺失。
- 继续复盘后确认是“迁移失败后的半成品表结构”导致；将回退策略改为“重置 sqlite 文件 + create_all”，并重启复验。
- 再次 `curl` 登录：`POST /api/v1/auth/login` 返回 `200`（token）。

4. Chrome E2E（MCP/DevTools）：
- 打开 `http://localhost:8089/login`，使用 `geyunfei / Gyf@845261` 登录。
- 成功进入首页（显示“欢迎, geyunfei”）。
- 点击进入 `/stories`，页面正常渲染“故事管理”。

## Next Steps
1. 为 lite 模式补一个自动种子脚本（默认创建测试管理员），减少手动初始化账号步骤。
2. 中长期将不兼容 SQLite 的 Alembic 迁移拆分或加分支，降低对 fallback 的依赖。

## Linked Commits
- pending (this commit)
