---
id: 2025-12-13T15-07-34Z-backend-virtual-ip-duplicate-name
date: 2025-12-13T15:07:34Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, virtual-ip]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip.py
  - ai-pic-backend/tests/unit/test_virtual_ip_unique_name.py
summary: "Handle duplicate virtual IP names gracefully and return 400 instead of crashing."
---

## User Prompt
现在 IP 创建有问题，解决

## Goals
- 修复虚拟IP创建时重复名称触发 unique 约束导致 500/Failed to fetch 的问题
- 创建/更新重复名称时返回可读错误（400 + detail）
- 增加最小自动化测试覆盖，减少回归风险

## Changes
- 后端：`POST /api/v1/virtual-ips/` 与 `PUT /api/v1/virtual-ips/{ip_id}` 在写库前做重复名校验，并捕获 `IntegrityError` 统一返回 `400 detail=虚拟IP名称已存在`
- 测试：新增用例验证创建/更新重复名称均返回 400

## Validation
- pytest：`cd ai-pic-backend && pytest tests/unit/test_virtual_ip_unique_name.py`
- Chrome E2E（http://localhost:8089）：
  - 使用账号 `geyunfei` 登录
  - 进入「虚拟IP」→「创建虚拟IP」
  - 输入已存在名称 `老拐` 点击创建，页面提示 `创建失败: 虚拟IP名称已存在`
  - DevTools Network 确认 `POST http://localhost:8000/api/v1/virtual-ips/` 返回 `400`，响应体 `{"detail":"虚拟IP名称已存在"}`

## Next Steps
- （可选）为 `create-with-ai` 路径也补齐 `IntegrityError` 的 400 映射，避免并发竞态下的 500
- （可选）梳理并分层跳过 external/e2e 测试，恢复 `pytest` 全量可用性作为回归门禁

## Linked Commits
- fix(backend): handle virtual ip duplicate names
