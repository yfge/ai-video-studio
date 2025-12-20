---
id: 2025-12-20T05-36-20Z-agents-build-script-path
date: 2025-12-20T05:36:20Z
participants: [human, codex]
models: [gpt-5]
tags: [docs, process]
related_paths:
  - AGENTS.md
summary: "Aligned AGENTS.md build script path with repo layout"
---
## User Prompt
Align the build script path in AGENTS.md (it says ./build_prod_images.sh but actual is ./docker/build_prod_images.sh), or add a root wrapper.

## Goals
- Fix the documented build script path to match the repo layout.

## Changes
- Updated AGENTS.md to reference `./docker/build_prod_images.sh` as the required pre-commit build script.

## Validation
- `./docker/build_prod_images.sh`

## Next Steps
- None.

## Linked Commits
- (pending)
