---
id: 2025-12-10T16-05-28Z-oss-manual-signing-import-fix
date: 2025-12-10T16:05:28Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, oss, bugfix]
related_paths:
  - ai-pic-backend/app/services/storage/oss_service.py
summary: "Fix missing imports in manual OSS signing path so environment image uploads no longer fail with NameError."
---

## User Prompt

- 用户贴出最新环境图日志，显示 `OSS 上传失败: name 'hmac' is not defined`，质疑上传逻辑是否彻底坏掉。

## Goals

- Fix the NameError introduced when switching OSS uploads to a manual HMAC-SHA1 signing implementation.
- Ensure the new upload path compiles and runs so that we see true OSS responses again (200 or 403), not local NameErrors.

## Changes

- Added missing `hmac` and `base64` imports at the top of `oss_service.py` required by the manual signing logic.
- Re-ran bytecode compilation for the module to confirm syntax correctness.

## Validation

- `cd ai-pic-backend && python -m py_compile app/services/storage/oss_service.py`
- `cd ai-pic-backend && pytest tests/unit/test_model_utils.py tests/unit/test_base_provider_client.py -q`
- Docker backend now starts without the previous SyntaxError/NameError; subsequent OSS logs will reflect real signature results instead of local import errors.

## Next Steps

- Observe the next environment image generation call to see whether OSS returns 200 or still reports SignatureDoesNotMatch with the new manual signing logic.

## Linked Commits

- pending
