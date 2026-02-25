"""
Scripts endpoints package.

Provides API routes for script management including CRUD, generation,
and storyboard operations.

Note: Storyboard task processors have been migrated to the
app.api.v1.endpoints.storyboard package. They are re-exported here
for backward compatibility with Celery workers and tests.
"""

# New script QC endpoints (kept out of scripts_legacy.py)
from app.api.v1.endpoints.scripts.audio_storyboard import (
    _process_script_audio_storyboard_task,
)
from app.api.v1.endpoints.scripts.audio_storyboard import (
    router as audio_storyboard_router,
)
from app.api.v1.endpoints.scripts.audio_timeline import (
    _process_script_audio_timeline_task,
)
from app.api.v1.endpoints.scripts.audio_timeline import router as audio_timeline_router
from app.api.v1.endpoints.scripts.dialogue_audio import (
    _process_script_dialogue_audio_task,
)
from app.api.v1.endpoints.scripts.dialogue_audio import router as dialogue_audio_router
from app.api.v1.endpoints.scripts.quality import router as quality_router
from app.api.v1.endpoints.scripts.timeline_pipeline import (
    _process_timeline_pipeline_task,
)
from app.api.v1.endpoints.scripts.timeline_pipeline import (
    router as timeline_pipeline_router,
)

# Import legacy router and NON-storyboard task helpers.
from app.api.v1.endpoints.scripts_legacy import (
    _populate_dialogues_and_stage_if_missing,
    _process_script_generation_task,
    _process_script_regeneration_task,
    _sync_script_scenes_to_story_structure,
)
from app.api.v1.endpoints.scripts_legacy import router as legacy_router  # noqa: F401

# Storyboard task processors now live in the storyboard package.
from app.api.v1.endpoints.storyboard import (  # noqa: F401
    _augment_frames,
    _enforce_storyboard_variety,
    _merge_frames,
    _process_storyboard_generation_task,
    _process_storyboard_image_task,
    _process_storyboard_video_task,
)

# Imported for test monkeypatching consistency across endpoint modules.
from app.services.ai_service import ai_service  # noqa: F401

# Mount non-legacy routers onto legacy_router (legacy contains "" paths).
legacy_router.include_router(quality_router)
legacy_router.include_router(dialogue_audio_router)
legacy_router.include_router(audio_timeline_router)
legacy_router.include_router(timeline_pipeline_router)
legacy_router.include_router(audio_storyboard_router)

# For now, expose the legacy router as the scripts router.
router = legacy_router

__all__ = [
    "router",
    "_augment_frames",
    "_enforce_storyboard_variety",
    "_merge_frames",
    "_populate_dialogues_and_stage_if_missing",
    "_process_script_audio_storyboard_task",
    "_process_script_audio_timeline_task",
    "_process_script_dialogue_audio_task",
    "_process_script_generation_task",
    "_process_script_regeneration_task",
    "_process_timeline_pipeline_task",
    "_process_storyboard_generation_task",
    "_process_storyboard_image_task",
    "_process_storyboard_video_task",
    "_sync_script_scenes_to_story_structure",
]
