---
id: 2025-12-04T07-47-26Z-email-validator
date: 2025-12-04T07:47:26Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, deps]
related_paths:
  - ai-pic-backend/requirements.txt
summary: "Add missing email-validator dependency for FastAPI/Pydantic"
---
## User Prompt
rocess SpawnProcess-1:
ai-video-backend   | Traceback (most recent call last):
ai-video-backend   |   File "/usr/local/lib/python3.11/site-packages/pydantic/networks.py", line 352, in import_email_validator
ai-video-backend   |     import email_validator
ai-video-backend   | ModuleNotFoundError: No module named 'email_validator'
...
除了nginx

## Goals
- Fix container boot failure caused by missing `email_validator` import required by Pydantic/FastAPI models.

## Changes
- Added `email-validator==2.1.0.post1` to backend `requirements.txt` so dev/prod builds include the package.

## Validation
- Not run here (dependency-only change); rerun docker dev stack build to pick up the new package.

## Next Steps
- Rebuild backend image via `cd docker && docker compose -f docker-compose.dev.yml build ai-video-backend` then restart stack.

## Linked Commits
- (pending)
