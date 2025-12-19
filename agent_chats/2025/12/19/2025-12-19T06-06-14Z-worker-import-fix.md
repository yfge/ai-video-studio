---
id: 2025-12-19T06-06-14Z-worker-import-fix
date: 2025-12-19T06:06:14Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, celery, imports]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/services/providers/openai_provider/__init__.py
summary: "Restore legacy task helper re-exports to fix Celery worker imports"
---

## User Prompt
"docker logs -f ai-video-celery-worker 现在worker 中一些导入 有问题，全局检查和处理这些问题"

## Goals
- Identify and fix worker import failures shown in Celery logs.
- Ensure legacy helper imports remain available after scripts refactor.

## Changes
- Re-exported legacy script task helpers from the scripts package to satisfy Celery worker imports.
- Re-exposed OpenAI schema helper utilities via provider package init to fix test imports.

## Validation
- `pytest` (timed out and multiple failures in this environment; see output in session).
- `./docker/build_prod_images.sh` (success; tag `42e70b1`).
- Chrome MCP: logged into `http://localhost:8089/login` with `geyunfei` / `Gyf@845261`, redirected to home dashboard.

## Next Steps
- Re-run `pytest` in the standard Python 3.11 environment and address any remaining failures.

## Linked Commits
- (pending)
