"""
Virtual IP Images API endpoints package.

Aggregates all virtual IP image sub-routers:
- crud: Basic CRUD operations (upload, list, get, update, delete)
- generation: AI text-to-image generation
- variants: Image-to-image variant generation
- async_tasks: Background task processors (for Celery workers)
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .generation import router as generation_router
from .variants import router as variants_router
from .async_tasks import (
    process_virtual_ip_image_task,
    process_virtual_ip_image_variant_task,
)

# Create main router and aggregate sub-routers
router = APIRouter()

# Append routes directly to avoid "Prefix and path cannot be both empty" error
for sub_router in [crud_router, generation_router, variants_router]:
    for route in sub_router.routes:
        router.routes.append(route)

__all__ = [
    "router",
    "process_virtual_ip_image_task",
    "process_virtual_ip_image_variant_task",
]
