from __future__ import annotations

from app.services.production_canvas.skills import list_canvas_skill_definitions


def test_canvas_skill_registry_maps_full_short_drama_chain_to_backend_reuse():
    skills = list_canvas_skill_definitions()

    assert [skill.id for skill in skills] == [
        "brief.compose",
        "asset.select",
        "script.generate",
        "storyboard.plan",
        "image.candidates",
        "video.candidates",
        "timeline.assemble",
        "report.summarize",
    ]
    targets = {target.target for skill in skills for target in skill.reuse_targets}
    assert (
        "app.services.storyboard.storyboard_image_autogen."
        "queue_storyboard_image_generation"
    ) in targets
    assert (
        "app.services.storyboard.video_generation_queue."
        "queue_storyboard_video_generation_task"
    ) in targets
    assert "app.services.timeline_pipeline_runner.run_timeline_main_chain" in targets
    assert (
        "app.services.timeline_render_dispatch.dispatch_timeline_render_job" in targets
    )
