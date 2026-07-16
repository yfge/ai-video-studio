from app.schemas.production_canvas import (
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteRequest,
)
from app.services.production_canvas.graph_runtime import resolve_canvas_graph_request


def test_approved_storyboard_resolves_as_video_reference_without_start_frame():
    state = ProductionCanvasSavedState.model_validate(
        {
            "graph_version": 2,
            "nodes": [
                {
                    "id": "storyboard",
                    "label": "Storyboard",
                    "title": "Clip storyboard",
                    "status": "approved",
                    "x": 0,
                    "y": 0,
                    "width": 200,
                    "skill": "storyboard.candidates",
                    "selected_output_id": 41,
                    "selected_output_url": "https://example.com/storyboard.png",
                    "output_ports": [{"id": "approved_storyboard", "type": "image"}],
                },
                {
                    "id": "video",
                    "label": "Video",
                    "title": "Video candidates",
                    "status": "ready",
                    "x": 240,
                    "y": 0,
                    "width": 200,
                    "skill": "video.candidates",
                    "input_ports": [
                        {
                            "id": "approved_storyboard",
                            "type": "image",
                            "required": True,
                        }
                    ],
                },
            ],
            "edges": [
                {
                    "edge_id": "storyboard-to-video",
                    "from": "storyboard",
                    "from_port": "approved_storyboard",
                    "to": "video",
                    "to_port": "approved_storyboard",
                    "binding_type": "selected_output",
                }
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
    )

    resolution = resolve_canvas_graph_request(
        state,
        ProductionCanvasSkillExecuteRequest(
            prompt="生成视频",
            skill="video.candidates",
            node_id="video",
        ),
    )

    assert resolution is not None
    assert resolution.resolved_inputs == {
        "approved_storyboard": "https://example.com/storyboard.png"
    }
    assert resolution.request.reference_artifacts == [
        "https://example.com/storyboard.png"
    ]
    assert resolution.request.start_frame_url is None
