---
id: 2025-12-11T21-15-30Z-storyboard-localhost-ref
date: 2025-12-11T21:15:30Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Rewrite localhost reference image URLs to INTERNAL_BACKEND_URL for storyboard img2img in containers"
---

## User Prompt
这是我实际的请求 ... reference_images 包含 http://localhost:8000/...，Celery worker 404 访问

## Goals
- Make storyboard img2img reference URLs reachable inside containers when users pass localhost URLs from the frontend.

## Changes
- Updated `_abs_url` in `scripts.py` to rewrite http://localhost/127.0.0.1 URLs to `INTERNAL_BACKEND_URL`, keeping path/scheme; other URLs unchanged.

## Validation
- Not run (logic change only); needs retry with localhost reference images.

## Next Steps
- [ ] Re-run storyboard img2img with localhost reference images to confirm they resolve to the backend host inside the worker.

## Linked Commits
- (pending)
