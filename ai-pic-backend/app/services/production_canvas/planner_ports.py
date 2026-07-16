from __future__ import annotations

from dataclasses import dataclass

from app.schemas.production_canvas import (
    CanvasBindingType,
    CanvasPortType,
    ProductionCanvasSavedPort,
)


@dataclass(frozen=True)
class CanvasPlannerBinding:
    from_port: str
    to_port: str
    binding_type: CanvasBindingType = "value"


def _port(
    port_id: str,
    port_type: CanvasPortType,
    *,
    required: bool = False,
) -> ProductionCanvasSavedPort:
    return ProductionCanvasSavedPort(
        id=port_id,
        type=port_type,
        required=required,
    )


SKILL_PORTS: dict[
    str, tuple[list[ProductionCanvasSavedPort], list[ProductionCanvasSavedPort]]
] = {
    "brief.compose": ([], [_port("production_brief", "contract")]),
    "content.plan": (
        [_port("production_brief", "contract", required=True)],
        [_port("production_context", "contract")],
    ),
    "asset.select": (
        [_port("production_context", "contract", required=True)],
        [
            _port("production_context", "contract"),
            _port("selected_assets", "entity_ref"),
            _port("virtual_ip", "entity_ref"),
            _port("environment", "entity_ref"),
        ],
    ),
    "virtual_ip.image": (
        [_port("virtual_ip", "entity_ref", required=True)],
        [_port("character_image", "image")],
    ),
    "environment.image": (
        [_port("environment", "entity_ref", required=True)],
        [_port("environment_image", "image")],
    ),
    "script.generate": (
        [_port("production_context", "contract", required=True)],
        [_port("script", "entity_ref")],
    ),
    "timeline.assemble": (
        [_port("script", "entity_ref", required=True)],
        [
            _port("timeline", "entity_ref"),
            _port("timeline_clip", "entity_ref"),
        ],
    ),
    "storyboard.plan": (
        [_port("script", "entity_ref", required=True)],
        [_port("storyboard_frame", "image")],
    ),
    "image.candidates": (
        [_port("script", "entity_ref", required=True)],
        [_port("approved_image", "image")],
    ),
    "storyboard.candidates": (
        [_port("timeline_clip", "entity_ref", required=True)],
        [_port("approved_storyboard", "image")],
    ),
    "video.candidates": (
        [
            _port("start_frame", "image"),
            _port("approved_storyboard", "image"),
        ],
        [_port("approved_video", "video")],
    ),
    "timeline.place": (
        [
            _port("timeline_clip", "entity_ref", required=True),
            _port("approved_video", "video", required=True),
        ],
        [_port("placed_timeline", "entity_ref")],
    ),
    "timeline.render": (
        [_port("timeline", "entity_ref", required=True)],
        [_port("rendered_video", "video")],
    ),
    "timeline.export": (
        [_port("rendered_video", "video", required=True)],
        [
            _port("exported_video", "video"),
            _port("delivery", "execution_ref"),
        ],
    ),
    "report.summarize": (
        [_port("execution", "execution_ref")],
        [_port("report", "execution_ref")],
    ),
}

ALLOWED_BINDINGS = {
    ("brief.compose", "content.plan"): CanvasPlannerBinding(
        "production_brief", "production_brief"
    ),
    ("content.plan", "asset.select"): CanvasPlannerBinding(
        "production_context", "production_context"
    ),
    ("asset.select", "script.generate"): CanvasPlannerBinding(
        "production_context", "production_context"
    ),
    ("asset.select", "virtual_ip.image"): CanvasPlannerBinding(
        "virtual_ip", "virtual_ip"
    ),
    ("asset.select", "environment.image"): CanvasPlannerBinding(
        "environment", "environment"
    ),
    ("script.generate", "timeline.assemble"): CanvasPlannerBinding("script", "script"),
    ("script.generate", "storyboard.plan"): CanvasPlannerBinding("script", "script"),
    ("script.generate", "image.candidates"): CanvasPlannerBinding("script", "script"),
    ("timeline.assemble", "storyboard.candidates"): CanvasPlannerBinding(
        "timeline_clip", "timeline_clip"
    ),
    ("storyboard.plan", "video.candidates"): CanvasPlannerBinding(
        "storyboard_frame", "start_frame"
    ),
    ("image.candidates", "video.candidates"): CanvasPlannerBinding(
        "approved_image", "start_frame", "selected_output"
    ),
    ("storyboard.candidates", "video.candidates"): CanvasPlannerBinding(
        "approved_storyboard", "approved_storyboard", "selected_output"
    ),
    ("timeline.assemble", "timeline.place"): CanvasPlannerBinding(
        "timeline_clip", "timeline_clip"
    ),
    ("video.candidates", "timeline.place"): CanvasPlannerBinding(
        "approved_video", "approved_video", "selected_output"
    ),
    ("timeline.assemble", "timeline.render"): CanvasPlannerBinding(
        "timeline", "timeline"
    ),
    ("timeline.place", "timeline.render"): CanvasPlannerBinding(
        "placed_timeline", "timeline"
    ),
    ("timeline.render", "timeline.export"): CanvasPlannerBinding(
        "rendered_video", "rendered_video"
    ),
    ("timeline.export", "report.summarize"): CanvasPlannerBinding(
        "delivery", "execution"
    ),
}

REQUIRED_DEPENDENCIES = {
    "content.plan": {"brief.compose"},
    "asset.select": {"content.plan"},
    "virtual_ip.image": {"asset.select"},
    "environment.image": {"asset.select"},
    "script.generate": {"asset.select"},
    "timeline.assemble": {"script.generate"},
    "storyboard.plan": {"script.generate"},
    "image.candidates": {"script.generate"},
    "storyboard.candidates": {"timeline.assemble"},
    "video.candidates": {"storyboard.candidates"},
    "timeline.place": {"timeline.assemble", "video.candidates"},
    "timeline.render": {"timeline.place"},
    "timeline.export": {"timeline.render"},
    "report.summarize": {"timeline.export"},
}

CANONICAL_DEPENDENCIES = {
    "brief.compose": [],
    "content.plan": ["brief.compose"],
    "asset.select": ["content.plan"],
    "script.generate": ["asset.select"],
    "timeline.assemble": ["script.generate"],
    "storyboard.candidates": ["timeline.assemble"],
    "video.candidates": ["storyboard.candidates"],
    "timeline.place": ["timeline.assemble", "video.candidates"],
    "timeline.render": ["timeline.place"],
    "timeline.export": ["timeline.render"],
    "report.summarize": ["timeline.export"],
}

CANONICAL_SKILLS = tuple(CANONICAL_DEPENDENCIES)
CANONICAL_MANIFEST_VERSION = "production_canvas.v2"


def canvas_skill_node_id(skill_id: str) -> str:
    return f"skill-{skill_id.replace('.', '-')}"


def canvas_skill_ports(
    skill_id: str,
    *,
    manifest_version: str | None = None,
) -> tuple[list[ProductionCanvasSavedPort], list[ProductionCanvasSavedPort]]:
    inputs, outputs = SKILL_PORTS[skill_id]
    if (
        manifest_version == CANONICAL_MANIFEST_VERSION
        and skill_id == "video.candidates"
    ):
        inputs = [_port("approved_storyboard", "image", required=True)]
    return (
        [port.model_copy(deep=True) for port in inputs],
        [port.model_copy(deep=True) for port in outputs],
    )


def planner_skill_catalog() -> list[dict]:
    return [
        {
            "id": skill_id,
            "allowed_dependencies": sorted(
                source for source, target in ALLOWED_BINDINGS if target == skill_id
            ),
            "required_dependencies": sorted(REQUIRED_DEPENDENCIES.get(skill_id, set())),
        }
        for skill_id in CANONICAL_SKILLS
    ]
