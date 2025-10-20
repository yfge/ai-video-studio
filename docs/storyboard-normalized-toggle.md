# Storyboard Normalized Toggle (Frontend)

An experimental toggle was added to the storyboard page to read normalized narrative structure (scenes and shots) from new backend endpoints without breaking the existing JSON-based storyboard flow.

Page: `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`

Behavior
- Default: OFF (existing behavior). When ON, the left scene list switches to normalized scenes and a compact shot summary appears above the storyboard frames.
- Selecting a normalized scene sets the visible storyboard scene via `scene_number`, keeping current frames UX unchanged.

Env flag
- `NEXT_PUBLIC_USE_NORMALIZED_BY_DEFAULT`: set to `true` to enable the toggle by default (otherwise OFF).

Endpoints used
- `/api/v1/story-structure/scripts/{script_id}/scenes`
- `/api/v1/story-structure/scenes/{scene_id}/shots`

Client helpers
- Implemented in `ai-pic-frontend/src/utils/api.ts` under `storyStructureAPI`.
