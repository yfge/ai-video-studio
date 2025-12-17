---
id: 2025-12-17T14-48-52Z-virtual-ip-oss-upload
date: 2025-12-17T14:48:52Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, virtual-ip, bugfix]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - tasks.md
summary: "Fix virtual IP manual upload to use correct OSS form data flow"
---

## User Prompt

现在 IP 管理中上传图像不好用，要走一下统一的 OSS。

## Goals

- 修复虚拟 IP 图像上传请求，确保使用统一的 OSS 上传通路。
- 避免 FormData 请求被错误的 Content-Type/字段名阻塞上传。

## Changes

- Updated `api.ts` request helper to skip JSON `Content-Type` for `FormData` and normalize headers safely before attaching auth.
- Corrected virtual IP image upload to send the file under `image`, normalize tag strings, and avoid JSON-string tags so backend OSS pipeline can parse inputs.
- Marked the virtual IP manual upload task as completed in `tasks.md`.

## Validation

- `npm run lint` (frontend) ✅
- Attempted to spin up a local mock backend for Chrome self-test, but the sandbox blocks opening listening sockets (`PermissionError: [Errno 1] Operation not permitted` when binding to 127.0.0.1/8000); no browser E2E possible in this environment.

## Next Steps

- Re-run a full browser upload flow against a real backend once a reachable service is available (login with geyunfei/Gyf@845261) to confirm OSS URLs are returned and displayed.

## Linked Commits

- TBC: virtual IP OSS upload form-data fixes
