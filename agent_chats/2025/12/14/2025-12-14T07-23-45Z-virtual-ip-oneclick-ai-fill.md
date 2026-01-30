---
id: 2025-12-14T07-23-45Z-virtual-ip-oneclick-ai-fill
date: "2025-12-14T07:23:45Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, backend, virtual-ip, ai-assist, prompt, ux]
related_paths:
  - ai-pic-frontend/src/app/virtual-ip/page.tsx
  - ai-pic-backend/app/prompts/templates/virtual_ip_creation.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_style_prompt.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_style_prompt.yaml
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/services/virtual_ip_ai_service.py
  - ai-pic-backend/tests/unit/test_virtual_ip_prompt_templates.py
summary: "One-click AI generation for Virtual IP creation with user brief input and improved prompt constraints."
---

## User Prompt

IP 创建时的 AI 辅助生成希望“点一次 AI，一次性生成并回填所有字段（描述/背景/小传/风格提示词），再允许逐项微调”。

## Goals

- 一次调用后端 AI 接口，生成并回填完整虚拟 IP 文案字段。
- 生成后用户可在表单内逐项编辑，不需要每个字段分别触发 AI。

## Changes

- 在名称下方新增「整体介绍」输入；点击「AI一键生成」时把该介绍作为上下文，调用 `generate-ai-content` 并回填 `description/background_story/biography/style_prompt`。
- 若用户已填写部分字段，点击生成会弹确认提示避免无意覆盖。
- 新增 `style_prompt` 字段编辑框，确保生成结果可见且可微调，并随创建请求一并提交。
- 优化后端提示词：
  - `virtual_ip_creation` 增加约束，禁止“虚拟IP/虚拟角色”元叙述与“{{name}}是一个...”模板句开头。
  - 新增 `virtual_ip_style_prompt` 并通过 `prompt_manager` 渲染，替换原先内联英文提示词拼接。
  - 输出后做轻量清洗，移除模型偶发输出的“虚拟IP/virtual ip”等词。

## Validation

- Frontend lint: `npm run lint`
- Backend unit: `pytest -q tests/unit/test_virtual_ip_prompt_templates.py`
- Chrome (MCP) E2E: 登录 `geyunfei` → 打开 `http://localhost:8089/virtual-ip` → 创建弹窗中先输入“整体介绍”（在名称下方）→ 点击「AI一键生成」→ 四个字段（角色描述/背景故事/人物小传/风格提示词）一次性回填成功，且输出不包含“虚拟IP/virtual ip”元叙述。

## Next Steps

- 如需保留“字段级 AI 再生成”，建议新增后端按字段生成的轻量接口，避免每次重新生成整套内容造成交互混乱。

## Linked Commits

- (pending)
