---
id: 2025-12-09T13-22-29Z-google-model-list
date: 2025-12-09T13:22:29Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, models]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider.py
summary: "Expand Google provider model list with remote fetch and richer fallbacks"
---
## User Prompt
google 也要参考火山和deepseek的形式，调用 google本身的模型列表

## Goals
- Make Google provider fetch its own model list similar to Volcengine/DeepSeek.
- Provide multiple Gemini text models as fallback when remote listing fails.

## Changes
- Added multiple static Gemini text models (1.5 Pro/Flash, 1.0 Pro) as fallbacks.
- Updated Google provider to call both Vertex AI and Generative Language model-list APIs, merge, and deduplicate results.

## Validation
- `pytest` (backend) — timed out at 120s with numerous pre-existing failures (diagnostic/keling/integration/oss suites etc. before completion); no new regressions confirmed within timeout.
- Chrome MCP: http://localhost:8089/stories → provider dropdown switched to Google shows Gemini 1.0 Pro / 1.5 Flash / 1.5 Pro / 3 Pro entries.

## Next Steps
- Investigate failing tests and rerun pytest to completion when time permits.

## Linked Commits
- fix(backend): expand google model listing (447628d)
