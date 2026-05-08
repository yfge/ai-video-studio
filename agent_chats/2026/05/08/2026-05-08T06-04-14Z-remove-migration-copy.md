## User Prompt

选择已迁移或已关联的故事 类似的“迁移” 之类的都去掉

## Goals

- Remove user-facing migration wording from the frontend production surfaces.
- Keep the change limited to copy and neutral component naming.
- Avoid touching backend database migration docs/API wording.

## Changes

- Replaced story list, workbench, environment, IP, and image-manager migration copy with production-focused wording.
- Renamed remaining frontend `MigrationNotice` component names to `ProductionNotice` so `ai-pic-frontend/src` no longer contains migration wording.

## Validation

- `rg -n "已迁移|迁移中|待迁移|迁移状态|从已迁移|migrat|migrate|Migration|migration" ai-pic-frontend/src -S`
  - Result: no matches.
- `cd ai-pic-frontend && npm run lint`
  - Result: passed with 19 existing warnings and 0 errors.

## Next Steps

- None.

## Linked Commits

- None
