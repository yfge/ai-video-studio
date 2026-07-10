from __future__ import annotations

import json
from types import SimpleNamespace

from app.models.script import Episode, Script, Story
from app.models.task import Task
from app.models.timeline import MediaAsset, RenderJob, Timeline
from app.models.user import User


def _create_timeline(db_session, user: User) -> tuple[Script, Timeline]:
    story = Story(user_id=user.id, title="Canvas render", genre="short_drama")
    db_session.add(story)
    db_session.commit()
    episode = Episode(story_id=story.id, episode_number=1, title="Pilot")
    db_session.add(episode)
    db_session.commit()
    script = Script(episode_id=episode.id, title="Pilot", content="Render it")
    db_session.add(script)
    db_session.commit()
    timeline = Timeline(
        episode_id=episode.id,
        script_id=script.id,
        title="Pilot Timeline",
        status="draft",
        version=3,
        spec={
            "fps": 24,
            "resolution": "768x768",
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [
                        {
                            "clip_id": "clip-1",
                            "start_ms": 0,
                            "end_ms": 1000,
                        }
                    ],
                }
            ],
        },
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(timeline)
    db_session.commit()
    db_session.refresh(timeline)
    return script, timeline


def test_canvas_render_and_export_reuse_current_timeline_job(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script, timeline = _create_timeline(db_session, user)
    monkeypatch.setattr(
        "app.services.production_canvas.render_execution."
        "TimelineResolvedVideoService.list_resolved_videos",
        lambda *_args, **_kwargs: SimpleNamespace(
            ready=True,
            video_clip_count=1,
            missing_clip_count=0,
            generating_clip_count=0,
        ),
    )
    monkeypatch.setattr(
        "app.services.timeline_service.dispatch_timeline_render_job",
        lambda *_args, **_kwargs: None,
    )

    request = {
        "prompt": "渲染当前成片",
        "skill": "timeline.render",
        "script_id": script.id,
        "run_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
    }
    response = client.post("/api/v1/production-canvas/execute", json=request)

    assert response.status_code == 200
    result = response.json()["data"]["skill_result"]
    assert result["skill"] == "timeline.render"
    assert result["status"] == "running"
    assert result["outputs"]["timeline_id"] == timeline.id
    assert result["outputs"]["timeline_version"] == 3
    render_job_id = result["outputs"]["render_job_id"]
    job = db_session.get(RenderJob, render_job_id)
    assert job.render_type == "final"
    assert job.preset == {"fps": 24, "resolution": "768x768"}

    repeated = client.post("/api/v1/production-canvas/execute", json=request)
    assert (
        repeated.json()["data"]["skill_result"]["outputs"]["render_job_id"]
        == render_job_id
    )

    job.status = "failed"
    job.log = {"code": "provider_failed"}
    db_session.add(job)
    db_session.commit()
    retried = client.post("/api/v1/production-canvas/execute", json=request)
    retried_job_id = retried.json()["data"]["skill_result"]["outputs"]["render_job_id"]
    assert retried_job_id != render_job_id
    assert db_session.get(RenderJob, render_job_id).is_deleted is True
    job = db_session.get(RenderJob, retried_job_id)
    render_job_id = retried_job_id

    asset = MediaAsset(
        asset_type="video",
        origin="rendered",
        file_url="https://example.test/final.mp4",
        mime_type="video/mp4",
        duration_ms=1000,
        created_by=user.id,
    )
    db_session.add(asset)
    db_session.commit()
    job.status = "succeeded"
    job.progress = 100
    job.output_asset_id = asset.id
    job.log = {"code": "render_succeeded", "clip_count": 1}
    db_session.add(job)
    db_session.commit()

    exported = client.post(
        "/api/v1/production-canvas/execute",
        json={**request, "skill": "timeline.export", "prompt": "导出成片"},
    )

    assert exported.status_code == 200
    export_result = exported.json()["data"]["skill_result"]
    assert export_result["status"] == "ready"
    assert export_result["outputs"]["render_job_id"] == render_job_id
    assert export_result["outputs"]["output_asset_id"] == asset.id
    assert export_result["outputs"]["output_url"] == asset.file_url


def test_canvas_run_restore_adds_render_and_export_nodes(
    client,
    db_session,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script, _timeline = _create_timeline(db_session, user)
    created = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "恢复旧生产画布", "script_id": script.id},
    ).json()["data"]
    run_task = db_session.get(Task, created["task_id"])
    payload = json.loads(run_task.parameters)
    removed_skills = {"timeline.render", "timeline.export"}
    payload["skill_manifest"]["skills"] = [
        item
        for item in payload["skill_manifest"]["skills"]
        if item["id"] not in removed_skills
    ]
    payload["skill_results"] = [
        item for item in payload["skill_results"] if item["skill"] not in removed_skills
    ]
    payload["nodes"] = [
        item for item in payload["nodes"] if item["skill"] not in removed_skills
    ]
    payload["saved_state"] = {
        "nodes": payload["nodes"],
        "edges": [],
        "viewport": {"x": 0, "y": 0, "zoom": 1},
        "selected_node_id": payload["nodes"][0]["id"],
    }
    run_task.parameters = json.dumps(payload)
    db_session.add(run_task)
    db_session.commit()

    restored = client.get(f"/api/v1/production-canvas/runs/{created['run_id']}").json()[
        "data"
    ]
    skills = [item["skill"] for item in restored["nodes"]]

    assert skills.index("timeline.assemble") < skills.index("storyboard.plan")
    assert skills.index("video.candidates") < skills.index("timeline.render")
    assert skills.index("timeline.render") < skills.index("timeline.export")
    render_node = next(
        item for item in restored["nodes"] if item["skill"] == "timeline.render"
    )
    assert render_node["status"] == "review"
    assert render_node["outputs"]["script_id"] == script.id
