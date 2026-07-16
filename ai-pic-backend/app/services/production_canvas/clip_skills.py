from app.schemas.production_canvas import (
    ProductionCanvasSkillDefinition,
    ProductionCanvasSkillReuseTarget,
)


def _service(label: str, target: str) -> ProductionCanvasSkillReuseTarget:
    return ProductionCanvasSkillReuseTarget(
        kind="service",
        label=label,
        target=target,
    )


CLIP_SKILL_DEFINITIONS = [
    ProductionCanvasSkillDefinition(
        id="storyboard.candidates",
        label="Clip Storyboard Candidates",
        description="Generate and review a 2/4/6/9-panel sheet for one Timeline clip.",
        reuse_targets=[
            _service(
                "Clip storyboard sheet",
                "app.services.storyboard.grid_storyboard_sheet_service."
                "GridStoryboardSheetService",
            )
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="timeline.place",
        label="Timeline Placement",
        description="Place an approved video into its stable Timeline clip.",
        reuse_targets=[
            _service(
                "Canvas Timeline placement",
                "app.services.production_canvas.timeline_placement."
                "place_canvas_video_in_timeline",
            )
        ],
    ),
]
