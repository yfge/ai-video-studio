---
id: 2025-12-20T05-56-16Z-virtual-ip-prompt-separation
date: 2025-12-20T05:56:16Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, prompts, virtual-ip]
related_paths:
  - ai-pic-backend/app/prompts/templates/virtual_ip_creation.txt
summary: "Clarified virtual IP creation prompt to enforce field-only content"
---

## User Prompt

调整创建人物 IP 时 "AI生成的提示词“，确保人物形象就是人物形象，完全的形象描写，背景故事就是背景故事 其他内容字段一样进行处理，保证 结构化的准确

## Goals

- 强化虚拟 IP 生成提示词的字段边界，避免混写
- 保持 JSON 结构输出准确

## Changes

- 收紧 `virtual_ip_creation` 模板的字段约束，逐项说明每个字段只写对应内容

## Validation

- `pytest` (fails: missing fixtures/external deps; many existing failures)
- `./docker/build_prod_images.sh`
- Chrome MCP: navigate to `http://localhost:3000` failed with `ERR_CONNECTION_REFUSED` (service not running)

## Next Steps

- 在可用的本地/测试环境补跑 Chrome 端到端创建虚拟 IP 流程并记录结果
- 复核现有 pytest 失败原因并修复或调整测试环境

## Linked Commits

- pending
