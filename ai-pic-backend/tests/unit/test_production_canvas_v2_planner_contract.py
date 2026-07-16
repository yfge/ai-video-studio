from __future__ import annotations

from app.services.production_canvas.planner_contracts import (
    canonical_canvas_planner_proposal,
    compile_canvas_planner_edges,
)
from app.services.production_canvas.planner_ports import (
    ALLOWED_BINDINGS,
    CANONICAL_MANIFEST_VERSION,
    SKILL_PORTS,
    canvas_skill_ports,
    planner_skill_catalog,
)


def test_canonical_canvas_v2_uses_clip_storyboard_without_keyframes():
    proposal = canonical_canvas_planner_proposal("生成故事板驱动的完整成片")
    edges = compile_canvas_planner_edges(proposal)

    assert [step.skill for step in proposal.steps] == [
        "brief.compose",
        "content.plan",
        "asset.select",
        "script.generate",
        "timeline.assemble",
        "storyboard.candidates",
        "video.candidates",
        "timeline.place",
        "timeline.render",
        "timeline.export",
        "report.summarize",
    ]
    bindings = {
        (edge.from_node, edge.from_port, edge.to_node, edge.to_port, edge.binding_type)
        for edge in edges
    }
    assert (
        "skill-timeline-assemble",
        "timeline_clip",
        "skill-storyboard-candidates",
        "timeline_clip",
        "value",
    ) in bindings
    assert (
        "skill-storyboard-candidates",
        "approved_storyboard",
        "skill-video-candidates",
        "approved_storyboard",
        "selected_output",
    ) in bindings
    assert (
        "skill-video-candidates",
        "approved_video",
        "skill-timeline-place",
        "approved_video",
        "selected_output",
    ) in bindings
    assert all(edge.to_port != "start_frame" for edge in edges)
    inputs, _ = canvas_skill_ports(
        "video.candidates",
        manifest_version=CANONICAL_MANIFEST_VERSION,
    )
    assert [(port.id, port.required) for port in inputs] == [
        ("approved_storyboard", True)
    ]


def test_v2_catalog_hides_legacy_keyframe_skills_but_keeps_v1_ports():
    assert [item["id"] for item in planner_skill_catalog()] == [
        "brief.compose",
        "content.plan",
        "asset.select",
        "script.generate",
        "timeline.assemble",
        "storyboard.candidates",
        "video.candidates",
        "timeline.place",
        "timeline.render",
        "timeline.export",
        "report.summarize",
    ]
    assert "storyboard.plan" in SKILL_PORTS
    assert "image.candidates" in SKILL_PORTS
    assert ("image.candidates", "video.candidates") in ALLOWED_BINDINGS
    legacy_inputs, _ = canvas_skill_ports("video.candidates")
    assert [port.id for port in legacy_inputs] == [
        "start_frame",
        "approved_storyboard",
    ]
