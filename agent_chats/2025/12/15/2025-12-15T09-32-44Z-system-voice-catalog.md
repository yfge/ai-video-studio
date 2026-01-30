---
id: 2025-12-15T09-32-44Z-system-voice-catalog
date: 2025-12-15T09:32:44Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, voice, virtual-ip]
related_paths:
  - ai-pic-backend/app/services/voice_catalog.py
  - ai-pic-backend/app/services/voice_service.py
  - ai-pic-backend/app/services/providers/minimax_provider.py
  - ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Add full MiniMax system voice catalog, expose via enums/fallback, and ensure frontend token load + voice options fallback."
---

## User Prompt

继续完善虚拟IP语音绑定：使用系统音色列表，按 provider/model/voice 提供列表并可试听。

## Goals

- Provide full MiniMax系统音色清单（中英文+语言）作为后端枚举/兜底。
- Ensure voice list/enums are available even when远端API需鉴权；前端能加载token并展示音色选项。
- Keep voice binding UI functional for provider-model-voice with preview.

## Changes

- Added `voice_catalog.py` with全量系统音色列表；`VoiceService` enums now expose `system_voices` and fall back to static catalog for system voices; Minimax provider also falls back when远端列表缺失。
- Frontend API types include `system_voices`; voice options fallback to catalog when远端列表为空；page mounts now refresh auth token.

## Validation

- `python -m black app/services/voice_catalog.py app/services/voice_service.py app/services/providers/minimax_provider.py`
- `npm run lint` (frontend) ✅
- Manual Chrome MCP: logged in at `http://localhost:8089/`, opened虚拟IP详情页；token set manually for this session (front now reloads token on mount).
- Backend `pytest` still failing overall (legacy/env issues); not rerun in this incremental step.

## Next Steps

- Re-run `/api/v1/voice/voices` after login to confirm system catalog populates dropdown; retry preview and save binding.
- Backend pytest and E2E Chrome run for IP语音绑定 once services stable.

## Linked Commits

- (this commit)
