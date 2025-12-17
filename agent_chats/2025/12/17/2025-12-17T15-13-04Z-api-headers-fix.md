---
id: 2025-12-17T15-13-04Z-api-headers-fix
date: 2025-12-17T15:13:04Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, bugfix]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
summary: "Fix FormData header typing to satisfy lint/type check"
---

## User Prompt

19.22 ./src/utils/api.ts:789:7 Type error: Type '{ "Content-Type"?: undefined; } | { "Content-Type": string; }' is not assignable to type 'HeadersInit | undefined'.

## Goals

- Resolve the TypeScript header typing issue introduced by the FormData-aware request helper.

## Changes

- Added header sanitization in the request helper to drop non-string/undefined values before passing to fetch, ensuring `HeadersInit` stays `Record<string, string>`.

## Validation

- `npm run lint` ✅

## Next Steps

- None; ready to proceed with normal flows.

## Linked Commits

- TBC: sanitize headers to fix FormData typing
