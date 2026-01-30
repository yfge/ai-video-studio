---
id: 2025-12-18T03-25-45Z-fix-ai-provider-jwt
date: 2025-12-18T03:25:45Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-providers]
related_paths:
  - ai-pic-backend/requirements.txt
summary: "Unblocked AI provider discovery by bundling PyJWT dependency for Keling provider and rebuilt images."
---

## User Prompt

后端 配置一直没有改动过，之前是好用的 ，所以这一块一定是有问题！ **不要嘴硬，不要嘴硬**

## Goals

- Restore `/api/v1/ai/models/available` from 503 by fixing backend provider initialization.
- Verify container loads providers without fallback and models list is available.
- Rebuild production images after dependency fix.

## Changes

- Added `PyJWT` to backend requirements so Keling provider auth module imports successfully (was crashing AIServiceManager init).
- Rebuilt prod images (tag 086fc23) after the dependency change.
- Hot-fixed running container by installing PyJWT and restarting services (mysql/redis/backend/worker) to recover immediately.

## Validation

- `curl -X POST /api/v1/auth/login` with test account to obtain token → success.
- `curl /api/v1/ai/models/available?model_type=text_generation` with bearer token → returns model list (DeepSeek/OpenAI/Google/Volcengine etc.), no 503.
- `./docker/build_prod_images.sh` — pass (backend/frontend images pushed tag 086fc23).

## Next Steps

- Consider disabling `UVICORN_RELOAD` in production to avoid reloader churn; noisy warnings remain for async voice/model cache but not blocking.

## Linked Commits

- (pending)
