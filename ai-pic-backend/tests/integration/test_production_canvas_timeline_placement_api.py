from __future__ import annotations

from app.models.script import Episode, Script, Story
from app.models.user import User

CLIP_A = "video_scene_001_beat_001_001"
CLIP_B = "video_scene_001_beat_002_002"


def _create_script(db_session, user: User, clip_ids: tuple[str, ...]) -> Script:
    story = Story(user_id=user.id, title="Timeline 放置故事", genre="comedy")
    db_session.add(story)
    db_session.commit()
    episode = Episode(story_id=story.id, episode_number=1, title="Timeline 放置")
    db_session.add(episode)
    db_session.commit()
    frames = [
        {
            "description": f"候选镜头 {index + 1}",
            "duration_seconds": 2.8,
            "video_urls": [f"https://example.com/frame-{index + 1}.mp4"],
            "source": {"kind": "timeline_clip", "clip_id": clip_id},
        }
        for index, clip_id in enumerate(clip_ids)
    ]
    script = Script(
        episode_id=episode.id,
        title="Timeline 放置剧本",
        content="两个镜头",
        extra_metadata={"storyboard": {"frames": frames}},
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)
    return script


def _timeline_clip(clip_id: str, index: int) -> dict:
    start_ms = index * 2800
    beat_id = f"beat_{index + 1:03d}"
    return {
        "clip_id": clip_id,
        "track_type": "video",
        "scene_id": "scene_001",
        "beat_id": beat_id,
        "ordinal": index + 1,
        "start_ms": start_ms,
        "end_ms": start_ms + 2800,
        "duration_ms": 2800,
        "source": {
            "kind": "audio_timeline_beat",
            "scene_id": "scene_001",
            "beat_id": beat_id,
            "audio_timeline_version": 1,
        },
        "source_refs": {"scene_beat_id": beat_id},
        "asset_ref": None,
        "placeholder": True,
    }


def _create_timeline(client, script: Script, clip_ids: tuple[str, ...]) -> dict:
    response = client.post(
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
                "duration_ms": len(clip_ids) * 2800,
                "tracks": [
                    {
                        "track_type": "video",
                        "clips": [
                            _timeline_clip(clip_id, index)
                            for index, clip_id in enumerate(clip_ids)
                        ],
                    }
                ],
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _video_node(
    node_id: str,
    script_id: int,
    timeline_id: int,
    version: int,
    frame_index: int,
    clip_id: str,
) -> dict:
    return {
        "id": node_id,
        "label": "Video Candidates",
        "title": node_id,
        "status": "review",
        "x": frame_index * 300,
        "y": 0,
        "width": 220,
        "kind": "pipeline",
        "skill": "video.candidates",
        "outputs": {
            "story_id": 999999,
            "episode_id": 999998,
            "script_id": script_id,
            "timeline_id": timeline_id,
            "timeline_version": version,
            "clip_id": clip_id,
            "frame_indexes": [frame_index],
        },
        "definition_version": 1,
    }


def _prepare_run(client, script: Script, timeline: dict, clip_ids: tuple[str, ...]):
    plan = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "选片并放入 Timeline", "script_id": script.id},
    ).json()["data"]
    node_ids = ["video-review"] if len(clip_ids) == 1 else ["video-a", "video-b"]
    nodes = [
        _video_node(
            node_id,
            script.id,
            timeline["id"],
            timeline["version"],
            index,
            clip_id,
        )
        for index, (node_id, clip_id) in enumerate(zip(node_ids, clip_ids))
    ]
    nodes.append(
        {
            "id": "timeline-render",
            "label": "Timeline Render",
            "title": "渲染 Timeline",
            "status": "ready",
            "x": 600,
            "y": 0,
            "width": 220,
            "kind": "pipeline",
            "skill": "render.timeline",
            "outputs": {
                "script_id": script.id,
                "timeline_id": timeline["id"],
                "timeline_version": timeline["version"],
            },
            "definition_version": 1,
        }
    )
    saved = client.put(
        f"/api/v1/production-canvas/runs/{plan['run_id']}/state",
        json={
            "graph_version": 2,
            "nodes": nodes,
            "edges": [],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
            "selected_node_id": node_ids[0],
        },
    )
    assert saved.status_code == 200, saved.text
    return plan, node_ids


def _approve_and_place(client, run_id: str, node_id: str, version: int):
    base = f"/api/v1/production-canvas/runs/{run_id}/nodes/{node_id}"
    candidates = client.get(f"{base}/candidates").json()["data"]["candidates"]
    assert len(candidates) == 1
    approved = client.post(
        f"{base}/approval", json={"candidate_id": candidates[0]["asset_id"]}
    )
    assert approved.status_code == 200, approved.text
    placed = client.post(
        f"{base}/timeline-placement", json={"expected_version": version}
    )
    assert placed.status_code == 200, placed.text
    return candidates[0], placed.json()["data"]


def _node(run: dict, node_id: str) -> dict:
    return next(item for item in run["saved_state"]["nodes"] if item["id"] == node_id)


def test_scoped_video_nodes_keep_their_clip_lineage_after_sequential_placements(
    client, db_session
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script(db_session, user, (CLIP_A, CLIP_B))
    timeline = _create_timeline(client, script, (CLIP_A, CLIP_B))
    plan, (node_a_id, node_b_id) = _prepare_run(
        client, script, timeline, (CLIP_A, CLIP_B)
    )

    _, after_a = _approve_and_place(client, plan["run_id"], node_a_id, 1)
    node_a = _node(after_a, node_a_id)
    node_b = _node(after_a, node_b_id)
    assert node_a["outputs"]["clip_id"] == CLIP_A
    assert node_a["outputs"]["timeline_version"] == 2
    assert node_b["outputs"]["clip_id"] == CLIP_B
    assert node_b["outputs"]["timeline_version"] == 1

    _, after_b = _approve_and_place(client, plan["run_id"], node_b_id, 2)
    node_a = _node(after_b, node_a_id)
    node_b = _node(after_b, node_b_id)
    render = _node(after_b, "timeline-render")
    assert (node_a["outputs"]["clip_id"], node_a["outputs"]["timeline_version"]) == (
        CLIP_A,
        2,
    )
    assert (node_b["outputs"]["clip_id"], node_b["outputs"]["timeline_version"]) == (
        CLIP_B,
        3,
    )
    assert node_a["outputs"]["placed_timeline_clip_id"] == CLIP_A
    assert node_b["outputs"]["placed_timeline_clip_id"] == CLIP_B
    assert render["outputs"]["clip_id"] == CLIP_B
    assert render["outputs"]["timeline_version"] == 3
    assert after_b["resolved_context"]["clip_id"] == CLIP_B
    assert after_b["resolved_context"]["timeline_version"] == 3
    assert (
        after_b["resolved_context"]["story_id"]
        == db_session.get(Episode, script.episode_id).story_id
    )
    task_context = client.get(f"/api/v1/tasks/{plan['task_id']}").json()[
        "result_context"
    ]
    assert task_context["clip_id"] == CLIP_B
    assert task_context["timeline_version"] == 3
