from types import SimpleNamespace

from app.services.video.video_task_storyboard_updater import _build_updated_frame
from app.services.video.video_task_utils import build_parameters_payload


def test_video_branch_context_reaches_generated_candidate_lineage():
    branch = {
        "run_id": "canvas-run",
        "node_id": "video-review",
        "parent_candidate_id": 41,
        "instruction": "镜头运动更克制",
    }
    params = build_parameters_payload(
        "镜头运动更克制",
        "https://example.com/start.png",
        None,
        None,
        5,
        {"canvas_branch": branch},
    )
    assert params["canvas_branch"] == branch

    updated = _build_updated_frame(
        {},
        SimpleNamespace(task_id=88, provider="provider", model="video-model"),
        {
            "video_url": "https://example.com/branch.mp4",
            "provider_used": "provider",
            "model_used": "video-model",
        },
        params,
    )
    assert updated["canvas_candidate_lineage"] == [
        {
            "url": "https://example.com/branch.mp4",
            "run_id": "canvas-run",
            "node_id": "video-review",
            "parent_candidate_id": 41,
            "branch_task_id": 88,
            "branch_instruction": "镜头运动更克制",
        }
    ]
