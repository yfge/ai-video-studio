---
id: 2025-12-21T06-58-38Z-virtual-ip-ai-style-tags
date: 2025-12-21T06:58:38Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, frontend, virtual-ip, ai, refactor]
related_paths:
  - ai-pic-backend/app/api/v1/api.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip/ai.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip/crud.py
  - ai-pic-backend/app/prompts/templates/virtual_ip_style_prompt.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_style_prompt.yaml
  - ai-pic-backend/app/schemas/virtual_ip.py
  - ai-pic-backend/app/services/virtual_ip_ai_service.py
  - ai-pic-backend/app/services/virtual_ip/__init__.py
  - ai-pic-backend/app/services/virtual_ip/ai_prompt_helpers.py
  - ai-pic-backend/tests/unit/test_virtual_ip_prompt_templates.py
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPCreateModal.tsx
  - ai-pic-frontend/src/hooks/useVirtualIPCreateForm.ts
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/virtual-ip/createFormUtils.ts
  - ai-pic-frontend/src/utils/virtual-ip/types.ts
summary: "Switched AI style prompt to Chinese, backfilled tags, and removed unused style reference input"
---

## User Prompt
AI一键生成的风格提示词不用是英文，同时标签没有回写；风格参考图功能没用，去掉。

## Goals
- 让 AI 生成的风格提示词支持中文输出
- AI 一键生成回写标签
- 移除无效的风格参考图输入
- 拆分虚拟 IP 端点与 AI 服务辅助逻辑以满足文件大小限制

## Changes
- 拆分虚拟 IP API 为 `virtual_ip/crud.py` 与 `virtual_ip/ai.py` 并在路由聚合中挂载
- 将虚拟 IP AI 生成的模板/清洗/标签解析抽离到独立 helper 文件
- 风格提示词模板改为中文输出，测试同步更新
- AI 生成响应新增 tags 并在创建表单回写
- 移除创建弹窗里的风格参考图字段

## Validation
- `pytest` (timed out after collection)
- `npm run lint`
- `./docker/build_prod_images.sh`
- Chrome MCP: `http://localhost:3000/login` -> `ERR_CONNECTION_REFUSED` (service not running)

## Next Steps
- 启动服务后补跑虚拟 IP AI 一键生成并确认标签回写与中文风格提示词

## Linked Commits
- pending
