---
id: 2025-12-17T15-55-40Z-agents-build-check
date: 2025-12-17T15:55:40Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [process, docs]
related_paths:
  - AGENTS.md
summary: "Documented mandatory pre-commit build_prod_images step."
---

## User Prompt

Emphasize that production images must be built via script before commits.

## Goals

- Record the requirement to run `./docker/build_prod_images.sh` prior to every commit.
- Keep agent guidance and mirrors in sync.

## Changes

- Added explicit pre-commit build instruction to `AGENTS.md` (symlinked to CLAUDE.md/GEMINI.md).

## Validation

- `./docker/build_prod_images.sh` — pass (images tagged 92f9fba already built/pushed this session).

## Next Steps

- None.

## Linked Commits

- (pending)
