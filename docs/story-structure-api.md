# Story Structure (Normalized) - Minimal API

This document describes the minimal read/write endpoints added for the normalized narrative structure. These do not replace existing JSON fields yet; they coexist behind a separate route group.

Base prefix: `/api/v1/story-structure`

- GET `/scripts/{script_id}/scenes`
  - Lists normalized scenes for a given script.
- POST `/scripts/{script_id}/scenes`
  - Creates a normalized scene for a given script (payload: SceneCreate).
- POST `/scripts/{script_id}/seed-from-json?dry_run=false`
  - Seeds normalized scenes from `Script.scenes` JSON for the given script. Returns prepared/inserted counts. Use `dry_run=true` to preview.
- GET `/scenes/{scene_id}/beats`
  - Lists ordered beats for a given scene.
- GET `/scenes/{scene_id}/shots`
  - Lists shots for a given scene.
- POST `/scenes/{scene_id}/shots`
  - Creates a shot for a given scene (payload: ShotCreate).
- GET `/stories/{story_id}/treatments?latest_only=true|false`
  - Lists treatments (revisions) for a story; optionally only latest.
- POST `/stories/{story_id}/treatments`
  - Creates a new treatment revision for the story.

Notes
- Models align with Alembic revision `a1b2c3d4e5f6_add_story_structure_tables.py`.
- Script relationship uses `normalized_scenes` to avoid clashing with `Script.scenes` JSON.
- Frontend can call these endpoints via `storyStructureAPI` helpers in `ai-pic-frontend/src/utils/api.ts`.
