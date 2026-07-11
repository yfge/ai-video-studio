from __future__ import annotations

from app.models.script import Episode, Script, Story
from app.models.timeline import MediaAsset
from app.models.user import User


def _create_script(db_session, user: User) -> Script:
    story = Story(user_id=user.id, title="候选评审故事", genre="comedy")
    db_session.add(story)
    db_session.commit()
    episode = Episode(story_id=story.id, episode_number=1, title="候选评审")
    db_session.add(episode)
    db_session.commit()
    script = Script(
        episode_id=episode.id,
        title="候选评审剧本",
        content="一个镜头",
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "description": "旧镜头",
                        "image_url": "https://example.com/old.png",
                    },
                    {
                        "description": "程序员看向智能音箱",
                        "ai_prompt": "共享办公区里的智能音箱",
                        "duration_seconds": 2.8,
                        "image_url": "https://example.com/frame-2.png",
                        "start_image_urls": [
                            "https://example.com/frame-2.png",
                            "https://example.com/frame-2-latest.png",
                        ],
                        "source": {
                            "kind": "timeline_clip",
                            "clip_id": "video_scene_001_beat_002_002",
                        },
                    },
                ]
            }
        },
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)
    return script


def _review_state(script_id: int) -> dict:
    return {
        "graph_version": 2,
        "nodes": [
            {
                "id": "image-review",
                "label": "Image Candidates",
                "title": "图片候选",
                "status": "review",
                "x": 0,
                "y": 0,
                "width": 220,
                "kind": "pipeline",
                "skill": "image.candidates",
                "outputs": {"script_id": script_id, "frame_indexes": [1]},
                "definition_version": 1,
                "output_ports": [{"id": "approved_image", "type": "image"}],
            },
            {
                "id": "video-review",
                "label": "Video Candidates",
                "title": "视频候选",
                "status": "review",
                "x": 300,
                "y": 0,
                "width": 220,
                "kind": "pipeline",
                "skill": "video.candidates",
                "outputs": {"script_id": script_id},
                "definition_version": 1,
                "execution_input_fingerprint": "a" * 64,
                "input_ports": [
                    {"id": "start_frame", "type": "image", "required": True}
                ],
            },
        ],
        "edges": [
            {
                "edge_id": "image-to-video",
                "from": "image-review",
                "from_port": "approved_image",
                "to": "video-review",
                "to_port": "start_frame",
                "binding_type": "selected_output",
                "required": True,
            }
        ],
        "viewport": {"x": 0, "y": 0, "zoom": 1},
        "selected_node_id": "image-review",
    }


def test_candidate_approval_persists_asset_and_stales_downstream(
    client,
    db_session,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script(db_session, user)
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "评审第二个镜头", "script_id": script.id},
    )
    run_id = plan.json()["data"]["run_id"]
    saved = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=_review_state(script.id),
    )
    assert saved.status_code == 200

    listed = client.get(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/image-review/candidates"
    )
    assert listed.status_code == 200
    candidates = listed.json()["data"]["candidates"]
    assert [item["url"] for item in candidates] == [
        "https://example.com/frame-2.png",
        "https://example.com/frame-2-latest.png",
    ]
    assert db_session.query(MediaAsset).filter_by(asset_type="image").count() == 2

    approved = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/image-review/approval",
        json={"candidate_id": candidates[1]["asset_id"]},
    )
    assert approved.status_code == 200
    nodes = approved.json()["data"]["saved_state"]["nodes"]
    image = next(item for item in nodes if item["id"] == "image-review")
    video = next(item for item in nodes if item["id"] == "video-review")
    assert image["status"] == "approved"
    assert image["definition_version"] == 2
    assert image["selected_output_id"] == candidates[1]["asset_id"]
    assert image["selected_output_url"] == candidates[1]["url"]
    assert image["selected_output_reviewed_by"] == user.id
    assert image["selected_output_reviewed_at"]
    assert image["outputs"]["approved_image"] == candidates[1]["url"]
    assert len(image["execution_input_fingerprint"]) == 64
    assert video["status"] == "stale"

    restored = client.get(f"/api/v1/production-canvas/runs/{run_id}")
    restored_nodes = restored.json()["data"]["saved_state"]["nodes"]
    restored_image = next(
        item for item in restored_nodes if item["id"] == "image-review"
    )
    assert restored_image["selected_output_id"] == candidates[1]["asset_id"]
    relisted = client.get(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/image-review/candidates"
    )
    selected = [item["selected"] for item in relisted.json()["data"]["candidates"]]
    assert selected == [False, True]
