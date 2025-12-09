---
id: 2025-12-09T09-38-50Z-provider-timeout
date: 2025-12-09T09:38:50Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, reliability]
related_paths:
  - ai-pic-backend/app/services/providers/base.py
summary: "Increase default provider timeout to reduce OpenAI request timeouts"
---
## User Prompt
现在调用 openai时会超时 加大超时时间 ，其他模型也一样。

## Goals
- Reduce request timeout errors by increasing the default provider timeout used across providers.
- Keep behaviour consistent for OpenAI and other provider clients.

## Changes
- Raised `ProviderConfig.timeout` default from 60s to 180s so all provider clients inherit a longer request timeout window.

## Validation
- `cd ai-pic-backend && pytest tests/test_ai_service.py -q` (pass; warnings about deprecated pydantic config and unknown marks remain pre-existing)

## Next Steps
- Consider provider-specific timeout overrides per API performance profile.

## Linked Commits
- (this commit)
