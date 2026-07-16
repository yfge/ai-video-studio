from __future__ import annotations

from typing import Any

from app.models.user import User
from app.repositories.timeline_repository import TimelineClipAssetRepository
from app.schemas.production_canvas import (
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
)
from app.schemas.production_canvas_review import ProductionCanvasMediaCandidateList
from app.services.production_canvas.stale_runtime import canvas_stale_impact_nodes
from sqlalchemy.orm import Session

from .candidate_history import (
    load_canvas_candidate_history,
    materialize_canvas_candidate,
    remember_canvas_candidate_history,
)


def _string(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def list_clip_storyboard_candidates(
    db: Session,
    owner: User,
    run_id: str,
    node: ProductionCanvasSavedNode,
    state: ProductionCanvasSavedState,
) -> ProductionCanvasMediaCandidateList:
    timeline_id = node.outputs.get("timeline_id")
    clip_id = _string(node.outputs.get("clip_id"))
    if not isinstance(timeline_id, int) or clip_id is None:
        raise ValueError("canvas_timeline_not_bound")
    link = TimelineClipAssetRepository(db).get_latest_for_clip_role_any_version(
        timeline_id=timeline_id,
        clip_id=clip_id,
        asset_role="clip_storyboard_sheet",
    )
    asset = link.media_asset if link is not None else None
    url = _string(asset.file_url if asset else None) or _string(
        asset.file_path if asset else None
    )
    if asset is None or url is None:
        candidates = []
    else:
        metadata = (
            asset.extra_metadata if isinstance(asset.extra_metadata, dict) else {}
        )
        current = materialize_canvas_candidate(
            db,
            owner,
            media_type="image",
            url=url,
            frame_index=0,
            clip_id=clip_id,
            prompt=None,
            model=_string(metadata.get("model")),
            duration_seconds=None,
            selected_output_id=node.selected_output_id,
        )
        history = {
            item.asset_id: item
            for item in load_canvas_candidate_history(db, owner, run_id, node, "image")
        }
        candidates = [
            history.get(current.asset_id, current).model_copy(
                update={"selected": current.asset_id == node.selected_output_id}
            )
        ]
    remember_canvas_candidate_history(db, run_id, node, candidates)
    db.commit()
    return ProductionCanvasMediaCandidateList(
        node_id=node.id,
        selected_output_id=node.selected_output_id,
        stale_impact=(
            canvas_stale_impact_nodes(state, node.id) if node.selected_output_id else []
        ),
        candidates=candidates,
    )
