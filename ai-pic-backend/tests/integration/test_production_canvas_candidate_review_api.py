from __future__ import annotations

from app.models.script import Episode, Script, Story
from app.models.timeline import MediaAsset, TimelineClipAsset
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
                        "video_urls": ["https://example.com/frame-2.mp4"],
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


def _video_review_state(script_id: int, timeline_id: int, version: int) -> dict:
    state = _review_state(script_id)
    video = state["nodes"][1]
    video["outputs"] = {
        "script_id": script_id,
        "timeline_id": timeline_id,
        "timeline_version": version,
        "frame_indexes": [1],
    }
    state["nodes"] = [video]
    state["edges"] = []
    state["selected_node_id"] = "video-review"
    return state


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
    assert listed.json()["data"]["stale_impact"] == []
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
    relisted_data = relisted.json()["data"]
    selected = [item["selected"] for item in relisted_data["candidates"]]
    assert selected == [False, True]
    assert relisted_data["stale_impact"] == [
        {"node_id": "video-review", "title": "Video Candidates"}
    ]


def test_approved_video_is_explicitly_placed_in_versioned_timeline(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script(db_session, user)
    clip_id = "video_scene_001_beat_002_002"
    timeline_response = client.post(
        f"/api/v1/episodes/{script.episode_id}/timelines",
        json={
            "script_id": script.id,
            "spec": {
                "spec_version": "timeline.v1",
                "episode_id": script.episode_id,
                "script_id": script.id,
                "version": 1,
                "source_audio_timeline_version": 1,
                "fps": 24,
                "resolution": "1080x1920",
                "duration_ms": 2800,
                "tracks": [
                    {
                        "track_type": "video",
                        "clips": [
                            {
                                "clip_id": clip_id,
                                "track_type": "video",
                                "scene_id": "scene_001",
                                "beat_id": "beat_002",
                                "ordinal": 2,
                                "start_ms": 0,
                                "end_ms": 2800,
                                "duration_ms": 2800,
                                "source": {
                                    "kind": "audio_timeline_beat",
                                    "scene_id": "scene_001",
                                    "beat_id": "beat_002",
                                    "audio_timeline_version": 1,
                                },
                                "source_refs": {"scene_beat_id": "beat_002"},
                                "asset_ref": None,
                                "placeholder": True,
                            }
                        ],
                    }
                ],
            },
        },
    )
    assert timeline_response.status_code == 200, timeline_response.text
    timeline = timeline_response.json()
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "选片并放入 Timeline", "script_id": script.id},
    )
    run_id = plan.json()["data"]["run_id"]
    saved = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=_video_review_state(script.id, timeline["id"], timeline["version"]),
    )
    assert saved.status_code == 200
    candidates = client.get(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/video-review/candidates"
    ).json()["data"]["candidates"]
    approved = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/video-review/approval",
        json={"candidate_id": candidates[0]["asset_id"]},
    )
    assert approved.status_code == 200

    placed = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/video-review/timeline-placement",
        json={"expected_version": timeline["version"]},
    )
    assert placed.status_code == 200
    node = placed.json()["data"]["saved_state"]["nodes"][0]
    assert node["outputs"]["timeline_version"] == 2
    assert node["outputs"]["placed_timeline_clip_id"] == clip_id
    current = client.get(f"/api/v1/timelines/{timeline['id']}").json()
    clip = current["spec"]["tracks"][0]["clips"][0]
    assert current["version"] == 2
    assert clip["clip_id"] == clip_id
    assert clip["asset_ref"]["media_asset_id"] == candidates[0]["asset_id"]
    assert clip["asset_ref"]["url"] == candidates[0]["url"]
    lineage = client.get(
        f"/api/v1/timelines/{timeline['id']}/clip-assets",
        params={"timeline_version": 2, "clip_id": clip_id},
    ).json()["items"]
    assert lineage[0]["media_asset_id"] == candidates[0]["asset_id"]
    assert lineage[0]["asset_role"] == "generated_video"

    generated = MediaAsset(
        asset_type="video",
        origin="provider_rework",
        file_url="https://example.com/generated-v2.mp4",
        created_by=user.id,
    )
    db_session.add(generated)
    db_session.flush()
    db_session.add(
        TimelineClipAsset(
            timeline_id=timeline["id"],
            timeline_version=2,
            clip_id=clip_id,
            track_type="video",
            asset_role="generated_video",
            media_asset_id=generated.id,
            source="provider_rework",
            created_by=user.id,
        )
    )
    db_session.commit()
    relisted = client.get(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/video-review/candidates"
    ).json()["data"]["candidates"]
    assert relisted[-1]["url"] == "https://example.com/generated-v2.mp4"

    conflict = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/video-review/timeline-placement",
        json={"expected_version": timeline["version"]},
    )
    assert conflict.status_code == 409
