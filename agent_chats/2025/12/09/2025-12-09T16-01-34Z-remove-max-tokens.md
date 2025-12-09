---
id: 2025-12-09T16-01-34Z-remove-max-tokens
date: 2025-12-09T16:01:34Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-manager, providers]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-backend/app/services/providers/deepseek_provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/providers/minimax_provider.py
  - ai-pic-backend/app/services/virtual_ip_ai_service.py
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-backend/tests/test_models.py
summary: "Removed hardcoded max_tokens caps across AI manager/providers and relaxed request payloads to rely on model defaults"
---
## User Prompt
把所有的max_tokens的限制都去掉

## Goals
- Remove hardcoded max_tokens limits in story generation and provider calls.
- Ensure AI manager and API accept optional max_tokens while defaulting to provider/model limits.
- Keep diagnostics/tests in sync with the new behavior.

## Changes
- Made AI manager max_tokens optional and only forwarded when explicitly provided; cleaned story/storyboard flows to drop 4000/3000/2500 caps.
- Updated OpenAI/Google/DeepSeek/Volcengine/Minimax providers and virtual IP AI helpers to skip max_tokens in payloads; left model metadata intact.
- Adjusted AI provider API request schema plus diagnostics scripts and test factories/fixtures to remove max_tokens expectations.

## Validation
- pytest tests/test_models.py tests/test_migration_working.py (fails: many uniqueness constraint errors due to existing data in persistent test DB; no code crash).
- Chrome E2E (MCP): logged in as geyunfei, created async story "MaxTokens 移除验证" with DeepSeek auto model; success toast shown.

## Next Steps
- Re-run full pytest in a clean DB to confirm no uniqueness conflicts.
- Monitor story async tasks to verify no max_tokens param is sent to providers.

## Linked Commits
- 6372bc9
