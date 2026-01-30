# Storyboard Normalized Integration (Frontend)

The storyboard page always loads normalized scenes/shots when available. The old toggle has been removed; if normalized data is missing, the page falls back to legacy storyboard JSON.

Page: `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`

Behavior

- Fetches normalized scenes for the active script via `storyStructureAPI.getNormalizedScenes`.
- Scene navigation prefers normalized scenes; if none exist, it falls back to scene numbers in storyboard frames.
- Selecting a normalized scene loads:
  - shots via `storyStructureAPI.getNormalizedSceneShots`
  - beats via `storyStructureAPI.getNormalizedSceneBeats` (timeline summary + frame timing hints)
- Environment binding:
  - selection is driven by `scene.environment_id`
  - saving uses `storyStructureAPI.updateScene`
- Shot character binding:
  - saving uses `storyStructureAPI.updateSceneShot` with `character_ids`

Endpoints used

- `/api/v1/story-structure/scripts/{script_id}/scenes`
- `/api/v1/story-structure/scenes/{scene_id}/shots`
- `/api/v1/story-structure/scenes/{scene_id}/beats`
- `/api/v1/story-structure/scenes/{scene_id}` (update)
- `/api/v1/story-structure/shots/{shot_id}` (update)
- `/api/v1/story-structure/environments`
- `/api/v1/story-structure/environments/{env_id}/images`

Client helpers

- `ai-pic-frontend/src/utils/api.ts` (`storyStructureAPI`)
