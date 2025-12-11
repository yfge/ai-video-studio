---
id: 2025-12-11T20-58-40Z-async-img2img-backend-url
date: 2025-12-11T20:58:40Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, config]
related_paths:
  - ai-pic-backend/app/core/config.py
summary: "Ensure Celery img2img tasks resolve backend URL off localhost to keep reference images in async runs"
---

## User Prompt
现在所有的异步的图文生图任务 都没有把图片真正的传入，包括 IP 的图文生图，场景 的图文生图，分镜的图文生图，受影响的有google和火山引擎

## Goals
- Make async image-to-image tasks (IP/environment/storyboard) send reference images by pointing workers at a reachable backend host instead of localhost.

## Changes
- Normalized `INTERNAL_BACKEND_URL` and added container-aware resolution that falls back to the docker-compose service host when running in containers or when localhost is misconfigured; kept localhost for bare-metal dev.
- Added optional `CONTAINER_BACKEND_URL` override to customize the container fallback without code changes.

## Validation
- `python - <<'PY'` to confirm default resolves to `http://localhost:8000` outside containers: **pass**.
- `KUBERNETES_SERVICE_HOST=1 python - <<'PY'` to simulate container fallback (`None`, `localhost`, custom host) → resolves to `http://ai-video-backend:8000` unless an explicit non-localhost URL is provided: **pass**.
- Not yet run broader tests or Chrome end-to-end; needs verification against live async img2img flows.

## Next Steps
- [ ] Deploy/configure with correct internal backend URL (or `CONTAINER_BACKEND_URL`) and re-run async IP/environment/storyboard img2img tasks against Google/Volc to confirm reference images are sent.
- [ ] Run Chrome end-to-end check for an async img2img path once backend is reachable.

## Linked Commits
- 5066500 fix(backend): default internal backend url for workers
