from app.schemas.production_canvas import ProductionCanvasSkillReuseTarget


def skill_target(
    kind: str,
    label: str,
    target: str,
    description: str | None = None,
) -> ProductionCanvasSkillReuseTarget:
    return ProductionCanvasSkillReuseTarget(
        kind=kind,
        label=label,
        target=target,
        description=description,
    )
