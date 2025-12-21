---
id: 2025-12-20T07-21-27Z-virtual-ip-voice-preview-oss
date: 2025-12-20T07:21:27Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, backend, virtual-ip, voice, oss]
related_paths:
  - ai-pic-backend/app/api/v1/api.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_voice_samples.py
  - ai-pic-backend/app/repositories/__init__.py
  - ai-pic-backend/app/repositories/virtual_ip_repository.py
  - ai-pic-backend/app/services/virtual_ip_voice_sample_service.py
  - ai-pic-frontend/src/app/virtual-ip/page.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPCreateModal.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPVoicePreviewSection.tsx
  - ai-pic-frontend/src/hooks/useVirtualIPCreateForm.ts
  - ai-pic-frontend/src/hooks/useVoicePreview.ts
  - ai-pic-frontend/src/utils/virtual-ip/voiceSampleApi.ts
summary: "Added voice preview in create modal and OSS persistence for preview samples"
---

## User Prompt
创建虚拟 IP 的 Modal 需要补全字段、语音配置对齐，并新增试听且保存后转存 OSS 关联角色。

## Goals
- 在创建虚拟 IP 弹窗补充试听能力
- 保存时把试听音频转存 OSS 并写回角色语音配置
- 后端新增可复用的角色语音试听保存接口

## Changes
- 新增虚拟 IP 语音试听保存端点与服务，上传 OSS 并更新 voice_config
- 增加 VirtualIPRepository 用于按 ID / business_id 获取角色
- 创建弹窗新增试听区块与预览逻辑，保存时调用新接口

## Validation
- `pytest` (failed: suite-wide failures incl. missing fixtures, API status mismatches, and external service errors)
- `npm run lint`
- `./docker/build_prod_images.sh` (first run timed out; rerun succeeded)
- Chrome MCP: `http://localhost:3000/login` -> `ERR_CONNECTION_REFUSED` (service not running)

## Next Steps
- 启动前后端后补跑创建虚拟 IP 试听并保存到 OSS 的全流程
- 如需，补充后端测试并修复现有测试环境依赖

## Linked Commits
- pending
