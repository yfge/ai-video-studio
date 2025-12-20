---
id: 2025-12-20T06-43-33Z-virtual-ip-voice-config-align
date: 2025-12-20T06:43:33Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, virtual-ip, voice]
related_paths:
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPCreateModal.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPVoiceSettingsForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPVoiceConfigSection.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/index.ts
  - ai-pic-frontend/src/hooks/useVoiceConfigOptions.ts
summary: "Aligned create modal voice config with IP management selectors"
---

## User Prompt
语音配置需要对齐现在 IP 管理的语音配置

## Goals
- 让创建虚拟 IP 的语音配置字段与现有 IP 管理保持一致
- 使用相同的服务商/模型/声音类型/声音选择逻辑

## Changes
- 新增基于语音枚举与列表的选择组件，用下拉选择替换手动输入
- 增加 `useVoiceConfigOptions` hook 复用获取/筛选逻辑
- 移除旧的手动语音配置输入块

## Validation
- `npm run lint`
- `./docker/build_prod_images.sh`
- Chrome MCP: `http://localhost:3000/virtual-ip` -> `ERR_CONNECTION_REFUSED` (service not running)

## Next Steps
- 启动前后端后补跑虚拟 IP 创建流程并记录语音配置选择结果

## Linked Commits
- pending
