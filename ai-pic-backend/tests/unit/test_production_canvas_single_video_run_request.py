from app.schemas.production_canvas import (
    ProductionCanvasSavedNode,
    ProductionCanvasSkillExecuteRequest,
)
from app.services.production_canvas.run_requests import request_for_canvas_node_context


def test_canvas_node_request_preserves_single_video_planning_mode():
    request = request_for_canvas_node_context(
        ProductionCanvasSkillExecuteRequest(
            prompt="生成单条视频",
            skill="script.generate",
        ),
        ProductionCanvasSavedNode(
            id="single-video-script",
            label="Script",
            title="生成单条视频剧本",
            status="ready",
            x=0,
            y=0,
            width=220,
            skill="script.generate",
            outputs={"planning_mode": "single_video", "episode_id": 20},
        ),
        {},
    )

    assert request.planning_mode == "single_video"
    assert request.episode_id == 20
