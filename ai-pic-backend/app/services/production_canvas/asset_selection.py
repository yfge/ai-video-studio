from __future__ import annotations

from dataclasses import dataclass

from app.models.story_structure import Environment
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.repositories.environment_repository import EnvironmentRepository
from app.repositories.virtual_ip_environment_repository import (
    VirtualIPEnvironmentRepository,
)
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.production_canvas import (
    ProductionCanvasAssetSummary,
    ProductionCanvasPlanRequest,
    ProductionCanvasSelectedAssets,
)
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class CanvasAssetSelection:
    selected: ProductionCanvasSelectedAssets
    candidate_virtual_ips: list[ProductionCanvasAssetSummary]
    candidate_environments: list[ProductionCanvasAssetSummary]
    created_virtual_ip_ids: list[int] | None = None
    created_environment_ids: list[int] | None = None

    def outputs(self) -> dict[str, list[int]]:
        return {
            "virtual_ip_ids": [asset.id for asset in self.selected.virtual_ips],
            "environment_ids": [asset.id for asset in self.selected.environments],
            "candidate_virtual_ip_ids": [
                asset.id for asset in self.candidate_virtual_ips
            ],
            "candidate_environment_ids": [
                asset.id for asset in self.candidate_environments
            ],
            "created_virtual_ip_ids": self.created_virtual_ip_ids or [],
            "created_environment_ids": self.created_environment_ids or [],
        }


def clean_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def asset_summary(asset: VirtualIP | Environment) -> ProductionCanvasAssetSummary:
    return ProductionCanvasAssetSummary(
        id=int(asset.id),
        business_id=getattr(asset, "business_id", None),
        name=asset.name,
        description=getattr(asset, "description", None),
        category=getattr(asset, "category", None),
        tags=clean_list(getattr(asset, "tags", None)),
        reference_images=clean_list(getattr(asset, "reference_images", None)),
    )


def score_text_match(prompt: str, name: str | None, tags: list[str]) -> int:
    score = 0
    normalized = prompt.lower()
    if name and name.lower() in normalized:
        score += 100
    for tag in tags:
        if tag.lower() in normalized:
            score += 10
    return score


def _match_score(prompt: str, asset: VirtualIP | Environment) -> int:
    return score_text_match(prompt, asset.name, clean_list(asset.tags))


def _select_virtual_ips(
    repo: VirtualIPRepository,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> tuple[VirtualIP | None, list[VirtualIP]]:
    if request.virtual_ip_id:
        selected = repo.get_owned_by_id(request.virtual_ip_id, user)
        return selected, [selected]
    candidates = [
        asset
        for asset in repo.list_accessible(user=user, limit=200)
        if _match_score(request.prompt, asset) > 0
    ]
    if not candidates:
        return None, []
    selected = max(
        candidates,
        key=lambda item: (_match_score(request.prompt, item), int(item.id)),
    )
    return selected, candidates


def _default_rank(linked, item: Environment) -> tuple[int, int]:
    default = any(link.environment_id == item.id and link.is_default for link in linked)
    sort_order = next(
        (link.sort_order for link in linked if link.environment_id == item.id),
        0,
    )
    return (1 if default else 0, -sort_order)


def _select_linked_environment(
    request: ProductionCanvasPlanRequest,
    linked,
) -> tuple[Environment | None, list[Environment]]:
    linked_envs = [link.environment for link in linked if link.environment]
    if not linked_envs:
        return None, []
    scored = [
        (_match_score(request.prompt, item), *_default_rank(linked, item), item)
        for item in linked_envs
    ]
    matched = [entry for entry in scored if entry[0] > 0]
    if matched:
        return (
            max(matched, key=lambda entry: (entry[0], entry[1], entry[2]))[3],
            linked_envs,
        )
    return max(linked_envs, key=lambda item: _default_rank(linked, item)), linked_envs


def _select_environment(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
    virtual_ip: VirtualIP | None,
) -> tuple[Environment | None, list[Environment]]:
    env_repo = EnvironmentRepository(db)
    if request.environment_id:
        selected = env_repo.get_owned_by_identifier(request.environment_id, user)
        return selected, [selected]
    linked = []
    if virtual_ip:
        linked = VirtualIPEnvironmentRepository(db).list_for_virtual_ip(
            int(virtual_ip.id)
        )
    selected, candidates = _select_linked_environment(request, linked)
    if candidates:
        return selected, candidates
    if virtual_ip:
        return None, []
    candidates = [
        asset
        for asset in env_repo.list_accessible(user=user, limit=200)
        if _match_score(request.prompt, asset) > 0
    ]
    if not candidates:
        return None, []
    selected = max(
        candidates,
        key=lambda item: (_match_score(request.prompt, item), int(item.id)),
    )
    return selected, candidates


def select_canvas_assets(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> CanvasAssetSelection:
    virtual_ip, virtual_ip_candidates = _select_virtual_ips(
        VirtualIPRepository(db),
        user,
        request,
    )
    environment, environment_candidates = _select_environment(
        db,
        user,
        request,
        virtual_ip,
    )
    selected = ProductionCanvasSelectedAssets(
        virtual_ips=[asset_summary(virtual_ip)] if virtual_ip else [],
        environments=[asset_summary(environment)] if environment else [],
    )
    return CanvasAssetSelection(
        selected=selected,
        candidate_virtual_ips=[asset_summary(asset) for asset in virtual_ip_candidates],
        candidate_environments=[
            asset_summary(asset) for asset in environment_candidates
        ],
    )
