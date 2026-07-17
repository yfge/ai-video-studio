from __future__ import annotations

from dataclasses import dataclass

from app.schemas.production_canvas import ProductionCanvasPlanRequest


@dataclass(frozen=True)
class CanvasContentProvisioning:
    request: ProductionCanvasPlanRequest
    created_story_ids: list[int]
    created_episode_ids: list[int]
