from __future__ import annotations

from app.models.user import User
from app.schemas.production_canvas import ProductionCanvasSavedState

from .collaboration import append_canvas_activity

_DEFINITION_FIELDS = {"graph_version", "nodes", "edges", "sections"}


def record_definition_change(
    payload: dict,
    user: User,
    run_id: str,
    previous: ProductionCanvasSavedState | None,
    state: ProductionCanvasSavedState,
) -> bool:
    previous_definition = (
        previous.model_dump(mode="json", by_alias=True, include=_DEFINITION_FIELDS)
        if previous
        else None
    )
    next_definition = state.model_dump(
        mode="json", by_alias=True, include=_DEFINITION_FIELDS
    )
    if previous_definition == next_definition:
        return False
    append_canvas_activity(
        payload,
        user,
        "definition.saved",
        target_type="run",
        target_id=run_id,
        detail=f"graph_version={state.graph_version}",
    )
    return True
