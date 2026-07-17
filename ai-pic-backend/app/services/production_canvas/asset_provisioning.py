from __future__ import annotations

from app.models.story_structure import Environment
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment
from app.repositories.environment_repository import EnvironmentRepository
from app.repositories.virtual_ip_environment_repository import (
    VirtualIPEnvironmentRepository,
)
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_brief import ProductionCanvasAssetIntent
from app.services.production_canvas.asset_selection import (
    CanvasAssetSelection,
    select_canvas_assets,
)
from sqlalchemy.orm import Session


def _same_name(items, name: str | None):
    if not name:
        return None
    normalized = name.casefold()
    return next(
        (item for item in items if str(item.name).strip().casefold() == normalized),
        None,
    )


def _restore_or_add_link(
    db: Session,
    user: User,
    virtual_ip: VirtualIP,
    environment: Environment,
) -> bool:
    repo = VirtualIPEnvironmentRepository(db)
    link = repo.get_pair(
        virtual_ip_id=int(virtual_ip.id),
        environment_id=int(environment.id),
        include_deleted=True,
    )
    if link and not link.is_deleted:
        return False
    if link:
        link.is_deleted = False
        link.deleted_at = None
        link.deleted_by = None
        link.deleted_reason = None
        link.user_id = user.id
        link.virtual_ip_business_id = virtual_ip.business_id
        link.environment_business_id = environment.business_id
    else:
        db.add(
            VirtualIPEnvironment(
                user_id=user.id,
                virtual_ip_id=virtual_ip.id,
                virtual_ip_business_id=virtual_ip.business_id,
                environment_id=environment.id,
                environment_business_id=environment.business_id,
                usage_type="scene_pool",
                usage_note="由结构化生产上下文绑定",
            )
        )
    return True


def provision_missing_canvas_assets(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
    selection: CanvasAssetSelection,
    *,
    asset_intent: ProductionCanvasAssetIntent | None = None,
    explicit_environment_id: int | None = None,
    asset_policy: str = "reuse_preferred",
) -> tuple[ProductionCanvasPlanRequest, CanvasAssetSelection]:
    intent = asset_intent or ProductionCanvasAssetIntent()
    environment_name = next(iter(intent.environment_names), None)
    ip_repo = VirtualIPRepository(db)
    env_repo = EnvironmentRepository(db)
    force_new = asset_policy == "create_new"
    allow_create = asset_policy in {
        "reuse_preferred",
        "create_if_missing",
        "create_new",
    }
    virtual_ip = (
        ip_repo.get_owned_by_id(selection.selected.virtual_ips[0].id, user)
        if selection.selected.virtual_ips and not force_new
        else None
    )
    environment = (
        env_repo.get_owned_by_identifier(selection.selected.environments[0].id, user)
        if selection.selected.environments and not force_new
        else None
    )
    created_virtual_ip_ids: list[int] = []
    created_environment_ids: list[int] = []
    changed = False

    try:
        if (
            virtual_ip is None
            and request.virtual_ip_id is None
            and intent.virtual_ip_name
            and allow_create
        ):
            if not force_new:
                virtual_ip = _same_name(
                    ip_repo.list_accessible(user=user, limit=200),
                    intent.virtual_ip_name,
                )
            if virtual_ip is None:
                virtual_ip = VirtualIP(
                    user_id=user.id,
                    name=intent.virtual_ip_name,
                    description=intent.virtual_ip_description or request.prompt,
                    tags=["production-canvas"],
                    is_active=True,
                )
                db.add(virtual_ip)
                db.flush()
                created_virtual_ip_ids.append(int(virtual_ip.id))
                changed = True

        if (
            environment is None
            and request.environment_id is None
            and environment_name
            and allow_create
        ):
            if not force_new:
                environment = _same_name(
                    env_repo.list_accessible(user=user, limit=200),
                    environment_name,
                )
            if environment is None:
                environment = Environment(
                    user_id=user.id,
                    name=environment_name,
                    description=request.prompt,
                    tags=["production-canvas"],
                    extra_metadata={"source": "production_canvas_context"},
                )
                db.add(environment)
                db.flush()
                created_environment_ids.append(int(environment.id))
                changed = True

        if virtual_ip and environment and explicit_environment_id is None:
            changed = _restore_or_add_link(db, user, virtual_ip, environment) or changed
        if changed:
            db.commit()
    except Exception:
        db.rollback()
        raise

    updates = {}
    if virtual_ip is not None:
        updates["virtual_ip_id"] = int(virtual_ip.id)
    if environment is not None:
        updates["environment_id"] = int(environment.id)
    resolved = request.model_copy(update=updates) if updates else request
    selected = select_canvas_assets(db, user, resolved)
    return resolved, CanvasAssetSelection(
        selected=selected.selected,
        candidate_virtual_ips=selected.candidate_virtual_ips,
        candidate_environments=selected.candidate_environments,
        created_virtual_ip_ids=created_virtual_ip_ids,
        created_environment_ids=created_environment_ids,
    )
