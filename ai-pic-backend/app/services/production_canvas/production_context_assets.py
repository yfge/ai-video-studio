from __future__ import annotations

from app.schemas.production_canvas_content import (
    ProductionCanvasAssetAssociation,
    ProductionCanvasPlanningDraft,
)
from app.services.production_canvas.asset_selection import CanvasAssetSelection


def asset_associations(
    planning: ProductionCanvasPlanningDraft,
    selection: CanvasAssetSelection,
) -> list[ProductionCanvasAssetAssociation]:
    requested_environments = list(planning.brief.assets.environment_names)
    for environment in selection.selected.environments:
        if environment.name not in requested_environments:
            requested_environments.append(environment.name)
    return [
        _association(
            "virtual_ip",
            planning.brief.assets.virtual_ip_name,
            selection.selected.virtual_ips,
            selection.candidate_virtual_ips,
            selection.created_virtual_ip_ids or [],
        ),
        *[
            _association(
                "environment",
                requested_name,
                [
                    item
                    for item in selection.selected.environments
                    if item.name == requested_name
                ],
                selection.candidate_environments,
                selection.created_environment_ids or [],
            )
            for requested_name in requested_environments
        ],
    ]


def _association(kind, requested_name, selected, candidates, created_ids):
    asset = selected[0] if selected else None
    if asset:
        created = asset.id in created_ids
        return ProductionCanvasAssetAssociation(
            kind=kind,
            requested_name=requested_name,
            decision="created" if created else "reused",
            asset_id=asset.id,
            asset_name=asset.name,
            candidate_ids=[item.id for item in candidates],
            reason="未找到可复用资产后新建。" if created else "命中现有可访问资产。",
        )
    if candidates:
        return ProductionCanvasAssetAssociation(
            kind=kind,
            requested_name=requested_name,
            decision="ambiguous",
            candidate_ids=[item.id for item in candidates],
            reason="匹配到多个同等候选，等待用户选择，系统不会擅自关联。",
        )
    return ProductionCanvasAssetAssociation(
        kind=kind,
        requested_name=requested_name,
        decision="missing" if requested_name else "not_required",
        candidate_ids=[item.id for item in candidates],
        reason="尚未确定资产。" if requested_name else "本次目标未要求该类资产。",
    )
