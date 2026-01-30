---
id: 2026-01-30T11-34-54Z-backend-test-migration-stabilization
date: 2026-01-30T11:34:54Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, tests, migrations]
related_paths:
  - ai-pic-backend/alembic/versions/0002_add_user_management_fields.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip/crud.py
  - ai-pic-backend/app/core/migration_safety.py
  - ai-pic-backend/app/core/migrations.py
  - ai-pic-backend/app/models/base.py
  - ai-pic-backend/app/models/user.py
  - ai-pic-backend/app/models/virtual_ip.py
  - ai-pic-backend/app/services/episode/episode_generation_service.py
  - ai-pic-backend/tests/api/v1/test_diagnostic_endpoints.py
  - ai-pic-backend/tests/e2e/test_user_management_e2e.py
  - ai-pic-backend/tests/factories.py
  - ai-pic-backend/tests/fixtures/mock_ai_service.py
  - ai-pic-backend/tests/test_api.py
  - ai-pic-backend/tests/test_basic.py
  - ai-pic-backend/tests/test_fastapi_full_flow.py
  - ai-pic-backend/tests/test_migration_simple.py
  - ai-pic-backend/tests/test_migration_system.py
  - ai-pic-backend/tests/test_migration_working.py
  - ai-pic-backend/tests/test_migrations.py
  - ai-pic-backend/tests/test_models.py
  - ai-pic-backend/tests/test_models_simple.py
  - ai-pic-backend/tests/test_user_management.py
  - ai-pic-backend/tests/unit/core/test_middleware.py
summary: "Stabilize backend tests and SQLite migration coverage; align test fixtures with current API/schema behavior."
---

## User Prompt

提交已经有的更改，清理工作区（提交前需要确保后端测试与生产镜像构建通过）。

## Goals

- 修复后端全量 `pytest` 的不稳定失败点（日志捕获顺序依赖）。
- 让 SQLite 单测环境下的 Alembic 迁移覆盖可执行（避免 MySQL-only DDL 卡死）。
- 对齐测试用例/工厂与当前 API 返回结构、端点路径、模型字段和 soft-delete 约束。
- 在提交前完成生产镜像构建验证，避免“能测不能构建”。

## Changes

- 迁移兼容：
  - `0002_add_user_management_fields` 在 SQLite 下使用 `batch_alter_table`（FK/alter default），并修正 downgrade 对称性。
  - `tests/test_migration_simple.py` 在 SQLite 下仅升级到兼容的 revision。
  - `tests/test_migrations.py` 标记为 module-level skip（MySQL-only head 链不适用于 SQLite 单测）。
- 迁移系统修复：
  - `app/core/migrations.py` 统一通过 `autogenerate=` kw 调用 `command.revision`。
  - `app/core/migration_safety.py` 用 dialect 判断 MySQL（避免依赖 `settings.DATABASE_URL`）。
- 模型约束对齐：
  - `business_id` 增加 `unique=True`；`User`/`VirtualIP` 增加软删除语义下的复合唯一索引。
  - `User.can_login/is_account_locked` 改为与 `datetime.utcnow()` 比较（避免 SQLAlchemy 表达式泄露到运行期判断）。
- API/服务与测试夹具：
  - `virtual_ip/crud.py` 列表接口增加 `search` 参数过滤（测试覆盖）。
  - `episode_generation_service.py` 动态引用 `ai_service_module.ai_service`，提升测试 monkeypatch 兼容性。
  - 更新 mock AI fixture、API/模型/用户管理相关测试，使其与当前端点与 schema 一致。
  - `tests/unit/core/test_middleware.py` 增强日志断言：对抗全局 logging 状态污染导致的顺序依赖失败。

## Validation

- `cd ai-pic-backend && pytest --no-cov`（1101 passed, 21 skipped）。
- `./docker/build_prod_images.sh`（成功，IMAGE_TAG=6790954）。

## Next Steps

- 恢复并继续推进“提示词统一管理”（会从当前 stash 取回模板改动），按 `tasks.md` 原子化提交。

## Linked Commits

- (pending) 将在本次提交完成后补全。

