"""
Story Structure API endpoints package.

Aggregates all story structure sub-routers:
- scenes: Scene CRUD and structure operations
- beats: Scene beat CRUD operations
- shots: Shot CRUD operations
- environments: Environment CRUD operations
- environment_images: Environment image CRUD (upload, list, delete)
- environment_generation: Environment text-to-image generation
- environment_variants: Environment image-to-image variant generation
- treatments: Story treatment and step outline operations
- async_tasks: Background task processors (for Celery workers)
"""

from fastapi import APIRouter

from .scenes import router as scenes_router
from .beats import router as beats_router
from .shots import router as shots_router
from .environments import router as environments_router
from .environment_images import router as environment_images_router
from .environment_generation import router as environment_generation_router
from .environment_variants import router as environment_variants_router
from .treatments import router as treatments_router
from .async_tasks import (
    process_environment_image_task,
    process_environment_image_variant_task,
)

# Create main router and aggregate sub-routers
router = APIRouter()

# Append routes directly to avoid "Prefix and path cannot be both empty" error
for sub_router in [
    scenes_router,
    beats_router,
    shots_router,
    environments_router,
    environment_images_router,
    environment_generation_router,
    environment_variants_router,
    treatments_router,
]:
    for route in sub_router.routes:
        router.routes.append(route)

__all__ = [
    "router",
    "process_environment_image_task",
    "process_environment_image_variant_task",
]
