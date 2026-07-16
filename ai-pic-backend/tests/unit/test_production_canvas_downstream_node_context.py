from __future__ import annotations

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
)
from app.services.production_canvas import executor
from app.services.production_canvas.graph_runtime import resolve_canvas_graph_request


def _user(db) -> User:
    user = User(
        username="canvas_downstream_context_owner",
        email="canvas-downstream-context@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_downstream_execution_uses_each_scoped_nodes_own_configuration(
    db_session,
    monkeypatch,
):
    state = ProductionCanvasSavedState.model_validate(
        {
            "graph_version": 2,
            "nodes": [
                {
                    "id": "image-a",
                    "label": "Image A",
                    "title": "Image A",
                    "status": "ready",
                    "x": 0,
                    "y": 0,
                    "width": 220,
                    "kind": "pipeline",
                    "skill": "image.candidates",
                    "outputs": {
                        "production_brief": "A",
                        "frame_indexes": [0],
                        "model": "image-a-model",
                        "story_id": 61,
                        "episode_id": 175,
                        "script_id": 140,
                        "timeline_id": 501,
                        "timeline_version": 7,
                        "clip_id": "clip-a",
                    },
                    "output_ports": [{"id": "production_brief", "type": "text"}],
                },
                {
                    "id": "video-b",
                    "label": "Video B",
                    "title": "Video B",
                    "status": "ready",
                    "x": 260,
                    "y": 0,
                    "width": 220,
                    "kind": "pipeline",
                    "skill": "video.candidates",
                    "outputs": {
                        "frame_indexes": [1],
                        "model": "video-b-model",
                        "reference_artifacts": ["environment_images:13:1"],
                        "story_id": 61,
                        "episode_id": 175,
                        "script_id": 150,
                        "timeline_id": 600,
                        "timeline_version": 2,
                        "clip_id": "clip-b",
                    },
                    "input_ports": [
                        {"id": "production_brief", "type": "text", "required": False}
                    ],
                },
            ],
            "edges": [
                {
                    "edge_id": "a-to-b",
                    "from": "image-a",
                    "from_port": "production_brief",
                    "to": "video-b",
                    "to_port": "production_brief",
                    "binding_type": "value",
                }
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
    )
    request = ProductionCanvasSkillExecuteRequest(
        prompt="execute downstream",
        skill="image.candidates",
        node_id="image-a",
        execution_scope="downstream",
        frame_indexes=[0],
        model="request-a-model",
        script_id=140,
        timeline_id=501,
        timeline_version=7,
        clip_id="clip-a",
    )
    first = resolve_canvas_graph_request(state, request)
    assert first is not None
    captured: list[ProductionCanvasSkillExecuteRequest] = []

    monkeypatch.setattr(
        executor,
        "_validate_canvas_skill_request",
        lambda _db, _user, item: item,
    )

    def dispatch(_db, _user, item):
        captured.append(item)
        return ProductionCanvasSkillExecuteResponse(
            skill_result=ProductionCanvasSkillResult(
                skill=item.skill,
                label=item.skill,
                status="review",
                title=item.skill,
                detail="captured",
                outputs={"frame_indexes": item.frame_indexes},
            )
        )

    monkeypatch.setattr(executor, "_dispatch_canvas_skill", dispatch)
    response = executor._execute_downstream(
        db_session,
        _user(db_session),
        request,
        state,
        first,
    )

    assert response.execution_order == ["image-a", "video-b"]
    assert [item.node_id for item in captured] == ["image-a", "video-b"]
    target = captured[1]
    assert target.frame_indexes == [1]
    assert target.model == "video-b-model"
    assert target.reference_artifacts == ["environment_images:13:1"]
    assert target.script_id == 150
    assert target.timeline_id == 600
    assert target.timeline_version == 2
    assert target.clip_id == "clip-b"
