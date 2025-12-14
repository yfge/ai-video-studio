---
id: 2025-12-14T11-23-51Z-environment-oss-persist-guard
date: 2025-12-14T11:23:51Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, oss, environment]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Surface environment image persistence failures instead of silently skipping when OSS upload breaks."
---

## User Prompt
检查环境生文图以及环境图生图的文件有没有正确的上传到 OSS ，现在看的效果是有问题的

## Goals
- Ensure environment text-to-image and image-to-image generations fail loudly when persistence/OSS uploads break instead of returning success with empty images.
- Add visibility into skipped images so we can tell whether OSS uploads are succeeding.

## Changes
- Added logging and error tracking in `_download_and_attach` so persistence failures record the offending URL and raise when nothing is saved.
- Wrapped sync environment generation endpoints to surface persistence errors as HTTP 500 responses instead of silently returning empty results.

## Validation
- `cd ai-pic-backend && pytest tests/unit/test_model_utils.py tests/unit/test_base_provider_client.py -q`

## Next Steps
- Run a real environment 文生图/图生图 call in an OSS-enabled deployment to confirm uploads now either succeed or return a clear error instead of a silent empty list.

## Linked Commits
- (pending)
