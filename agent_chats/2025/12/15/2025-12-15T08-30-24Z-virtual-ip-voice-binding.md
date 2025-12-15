---
id: 2025-12-15T08-30-24Z-virtual-ip-voice-binding
date: 2025-12-15T08:30:24Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, backend, voice, virtual-ip]
related_paths:
  - ai-pic-backend/app/models/virtual_ip.py
  - ai-pic-backend/app/schemas/virtual_ip.py
  - ai-pic-backend/alembic/versions/1c2d3e4f5a67_add_voice_config_to_virtual_ips.py
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx
summary: "Add voice binding for Virtual IPs with MiniMax enums/preview and persisted voice_config."
---

## User Prompt
在 IP 详情页面上，加上语音设置，可以为一个角色绑定一个语音，并按 provider-model-roles 提供列表及试听服务。

## Goals
- Persist voice binding (provider/model/voice) on Virtual IP records.
- Surface voice provider/model/voice lists with bilingual labels and preview on IP detail page.
- Keep updates aligned with existing MiniMax voice endpoints and lint clean.

## Changes
- Backend: added `voice_config` JSON column to `virtual_ips` with schema exposure (`VirtualIPBase/Response`) and Alembic migration `1c2d3e4f5a67_add_voice_config_to_virtual_ips.py`.
- Frontend utils: introduced voice enums/list/preview APIs (`voiceAPI`) and voice-related types; `VirtualIP` create/update now carry `voice_config`.
- Virtual IP detail page: new “语音设置” section with provider/model/voice type/voice selectors, preview text input, audio preview, and save binding via update call.

## Validation
- `python -m black app/models/virtual_ip.py app/schemas/virtual_ip.py alembic/versions/1c2d3e4f5a67_add_voice_config_to_virtual_ips.py`
- `npm run lint` (ai-pic-frontend) ✅
- Not run: backend `pytest` / Alembic migration apply / browser E2E (time & env not set up yet).

## Next Steps
- Apply migration in target environment, then rerun backend tests.
- Run Chrome MCP E2E on IP详情页语音绑定与试听链路（使用 ge/yunfei 账号），记录结果。
- Align backend voice list (provider/model dictionaries) with any additional providers once available.

## Linked Commits
- (this commit)
