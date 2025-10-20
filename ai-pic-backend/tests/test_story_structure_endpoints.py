import pytest
from fastapi.routing import APIRoute

from app.main import create_app


@pytest.mark.unit
def test_story_structure_routes_present():
    app = create_app()
    paths = {r.path for r in app.routes if isinstance(r, APIRoute)}

    # Minimal presence checks (no DB required)
    assert "/api/v1/story-structure/scripts/{script_id}/scenes" in paths
    assert "/api/v1/story-structure/scenes/{scene_id}/beats" in paths
    assert "/api/v1/story-structure/scenes/{scene_id}/shots" in paths
    assert "/api/v1/story-structure/stories/{story_id}/treatments" in paths
    # creation endpoints present
    assert any(p for p in paths if p == "/api/v1/story-structure/scripts/{script_id}/scenes" and any(
        r.methods and "POST" in r.methods for r in app.routes if isinstance(r, APIRoute) and r.path == p
    ))
    assert any(p for p in paths if p == "/api/v1/story-structure/scenes/{scene_id}/shots" and any(
        r.methods and "POST" in r.methods for r in app.routes if isinstance(r, APIRoute) and r.path == p
    ))
    # seed endpoint present
    assert "/api/v1/story-structure/scripts/{script_id}/seed-from-json" in paths
