---
id: 2025-12-15T10-25-48Z-voice-preview-defaults
date: 2025-12-15T10:25:48Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, voice]
related_paths:
  - ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx
summary: "Harden voice defaults so preview/model selection works and add fallback provider handling."
---

## User Prompt

- 在 IP 详情页面上，加上语音设置，可以为一个角色绑定一个语音；选择不了模型/提示请选择模型问题。
- 试听失败: invalid params, type mismatch；现在选择不了模型了。
- Run backend pytest; 完成 IP 详情页语音绑定+试听 E2E 并记录。

## Goals

- Ensure voice provider/model/voice defaults are applied so users can preview without extra clicks.
- Keep voice type/filter in sync and allow preview with proper provider fallback.
- Validate via backend pytest and UI E2E.

## Changes

- Added `mergeVoiceSettings` helper to safely apply MiniMax defaults with incoming voice_config and keep provider/model/voice_type/voice_id populated.
- Synced voice_type filter with saved voice_config, reset voice_id on filter change, and set model fallback when provider changes.
- Updated preview handler to auto-fill provider/model/voice fallbacks before calling TTS.

## Validation

- `cd ai-pic-backend && pytest --maxfail=1` (fails: `tests/api/v1/test_diagnostic_endpoints.py::test_openai_test_endpoint_requires_auth` expected 401 got 200; numerous pre-existing warnings).
- `cd ai-pic-frontend && npm run lint`.
- Chrome MCP E2E @ http://localhost:8089/: logged in session, on IP详情页(id=1) selected provider MiniMax / model `speech-2.6-turbo` / voice `精英青年音色`, preview generated audio successfully (alert 成功 + audio player rendered).

## Next Steps

- Address failing diagnostic auth test returning 200 instead of 401.
- Consider confirming default voice preview works on fresh load after deploying build.

## Linked Commits

- (this commit)
