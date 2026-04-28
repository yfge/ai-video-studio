import pytest

from app.api.v1.api import api_router


@pytest.mark.unit
def test_scripts_router_exposes_storyboard_generation_route():
    route_paths = {getattr(route, "path", None) for route in api_router.routes}

    assert "/scripts/{script_id}/storyboard/generate-async" in route_paths
    assert "/scripts/{script_id}/storyboard/generate-images" in route_paths
    assert "/scripts/{script_id}/storyboard/generate-video" in route_paths
