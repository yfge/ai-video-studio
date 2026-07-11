from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.models.user import User
from app.schemas.production_canvas import ProductionCanvasRunResponse
from app.schemas.production_canvas_review import (
    ProductionCanvasTimelinePlacementRequest,
)
from app.schemas.timeline import TimelineUpdate
from app.services.timeline_service import TimelineService
from sqlalchemy.orm import Session

from .access_control import canvas_run_owner, require_canvas_access
from .run_persistence import load_canvas_saved_state, save_canvas_state


def _video_node(state, node_id: str):
    node = next((item for item in state.nodes if item.id == node_id), None)
    if node is None:
        raise ValueError("canvas_node_not_found")
    if node.skill != "video.candidates":
        raise ValueError("canvas_node_not_placeable")
    if node.status != "approved" or not node.selected_output_id:
        raise ValueError("canvas_video_not_approved")
    return node


def _replace_clip_asset(
    spec: dict[str, Any],
    *,
    clip_id: str,
    asset_id: int,
    asset_url: str,
    run_id: str,
    node_id: str,
) -> dict[str, Any]:
    updated = deepcopy(spec)
    for track in updated.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_type = track.get("track_type") or track.get("type")
        for clip in track.get("clips") or []:
            if not isinstance(clip, dict) or clip.get("clip_id") != clip_id:
                continue
            if (clip.get("track_type") or track_type) != "video":
                raise ValueError("canvas_timeline_clip_not_video")
            clip["asset_ref"] = {
                "kind": "production_canvas_approved_video",
                "media_asset_id": asset_id,
                "url": asset_url,
                "source": {"run_id": run_id, "node_id": node_id},
            }
            clip["placeholder"] = False
            return updated
    raise ValueError("canvas_timeline_clip_not_found")


def place_canvas_video_in_timeline(
    db: Session,
    user: User,
    run_id: str,
    node_id: str,
    request: ProductionCanvasTimelinePlacementRequest,
) -> ProductionCanvasRunResponse:
    require_canvas_access(db, user, run_id, "approve")
    owner = canvas_run_owner(db, user, run_id)
    state = load_canvas_saved_state(db, user, run_id)
    if state is None:
        raise ValueError("canvas_run_state_not_found")
    node = _video_node(state, node_id)
    timeline_id = node.outputs.get("timeline_id")
    clip_id = node.outputs.get("selected_output_clip_id")
    asset_url = node.selected_output_url
    if not isinstance(timeline_id, int):
        raise ValueError("canvas_timeline_not_bound")
    if not isinstance(clip_id, str) or not clip_id or not asset_url:
        raise ValueError("canvas_video_target_not_bound")

    service = TimelineService(db)
    timeline = service.get_timeline(timeline_id, owner)
    spec = _replace_clip_asset(
        timeline.spec,
        clip_id=clip_id,
        asset_id=node.selected_output_id,
        asset_url=asset_url,
        run_id=run_id,
        node_id=node_id,
    )
    placed = service.update_timeline(
        timeline_id,
        TimelineUpdate(expected_version=request.expected_version, spec=spec),
        owner,
    )
    updated_node = node.model_copy(
        update={
            "definition_version": node.definition_version + 1,
            "outputs": {
                **node.outputs,
                "timeline_id": placed.id,
                "timeline_version": placed.version,
                "placed_timeline_clip_id": clip_id,
                "placed_media_asset_id": node.selected_output_id,
            },
        }
    )
    next_state = state.model_copy(
        update={
            "nodes": [
                updated_node if item.id == node_id else item for item in state.nodes
            ]
        }
    )
    run = save_canvas_state(db, user, run_id, next_state, capability="approve")
    if run is None:
        raise ValueError("canvas_run_state_not_found")
    return run
