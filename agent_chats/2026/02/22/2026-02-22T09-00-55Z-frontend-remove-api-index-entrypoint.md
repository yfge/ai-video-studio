---
id: 2026-02-22T09-00-55Z-frontend-remove-api-index-entrypoint
date: 2026-02-22T09:00:55Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, "[refactor]"]
related_paths:
  - ai-pic-frontend/src/utils/api/index.ts
  - ai-pic-frontend/src/app/test-auth/page.tsx
  - ai-pic-frontend/src/utils/auth.ts
  - tasks.md
summary: "Removed legacy src/utils/api/index.ts entrypoint and fixed remaining runtime references to modular API imports."
---

## User Prompt

继续

## Goals

- Continue the frontend API modularization by removing `src/utils/api/index.ts`.
- Fix hidden runtime/type references that still depended on the legacy index entrypoint.
- Re-validate key user paths and build/lint gates before committing.

## Changes

- Deleted legacy API entrypoint:
  - `ai-pic-frontend/src/utils/api/index.ts`
- Updated dynamic API import in test page:
  - `ai-pic-frontend/src/app/test-auth/page.tsx`
  - `import("../../utils/api")` -> `import("@/utils/api/endpoints")`
- Updated auth type import to modular types barrel:
  - `ai-pic-frontend/src/utils/auth.ts`
  - `import type { User } from "@/utils/api/types"`
- Updated migration status text in `tasks.md` to reflect both legacy entry files removed:
  - `src/utils/api.ts` and `src/utils/api/index.ts`

## Validation

- Frontend lint:
  - `cd ai-pic-frontend && npm run lint` => pass (warnings only).
- Production image gate:
  - `./docker/build_prod_images.sh` => build reaches image export/push stage but fails on registry network/auth transport (`TLS handshake timeout`, `connection reset by peer`, `broken pipe`) when pushing to `registry.cn-beijing.aliyuncs.com`.
  - Failure is in external registry connectivity during `--push`, not in frontend compile/import resolution.
- Chrome MCP E2E:
  - Opened `/login`, logged in with `geyunfei` and reached `/` dashboard (verified `虚拟IP管理` section).
  - Opened `/test-auth`, clicked `测试 API 客户端登录`; request executed and returned backend `401 Unauthorized` (expected auth outcome for the hardcoded test credentials), confirming no runtime module import failure after index removal.

## Next Steps

- Re-run `./docker/build_prod_images.sh` when Aliyun registry connectivity is stable to complete the push gate.
- Continue remaining frontend modular refactor items in `tasks.md`.

## Linked Commits

- refactor(frontend): remove api index entrypoint
