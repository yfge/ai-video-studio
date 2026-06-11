from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.schemas.virtual_ip import (
    VirtualIPCreate,
    VirtualIPReadiness,
    VirtualIPResponse,
    VirtualIPUpdate,
)
from app.services.virtual_ip_readiness import compute_virtual_ip_readiness
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

router = APIRouter()


def _not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def _get_owned_virtual_ip(
    db: Session,
    current_user: User,
    ip_id: int | None,
    ip_business_id: str | None = None,
) -> VirtualIP:
    """获取当前用户可访问的虚拟 IP（支持 business_id）。"""
    query = _not_deleted(db.query(VirtualIP), VirtualIP)
    if ip_business_id:
        query = query.filter(VirtualIP.business_id == ip_business_id)
    elif ip_id is not None:
        query = query.filter(VirtualIP.id == ip_id)
    else:
        raise HTTPException(status_code=400, detail="虚拟IP标识缺失")
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(VirtualIP.user_id == current_user.id)
    ip = query.first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    return ip


@router.get("/")
def list_virtual_ips(
    skip: int = 0,
    limit: int = 20,
    business_id: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = _not_deleted(db.query(VirtualIP), VirtualIP)
    if business_id:
        query = query.filter(VirtualIP.business_id == business_id)
    if search:
        query = query.filter(VirtualIP.name.contains(search.strip()))
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(VirtualIP.user_id == current_user.id)
    virtual_ips = query.order_by(VirtualIP.id.desc()).offset(skip).limit(limit).all()
    return {
        "success": True,
        "data": [VirtualIPResponse.from_orm(ip) for ip in virtual_ips],
    }


@router.get("", include_in_schema=False)
def list_virtual_ips_no_slash(
    skip: int = 0,
    limit: int = 20,
    business_id: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    兼容无尾斜杠的 /api/v1/virtual-ips 请求，避免 307 重定向。

    内部直接复用 list_virtual_ips 的分页与权限逻辑。
    """
    return list_virtual_ips(
        skip=skip,
        limit=limit,
        business_id=business_id,
        search=search,
        current_user=current_user,
        db=db,
    )


@router.post("/")
def create_virtual_ip(
    ip: VirtualIPCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    existing_ip = (
        _not_deleted(db.query(VirtualIP), VirtualIP)
        .filter(VirtualIP.name == ip.name)
        .first()
    )
    if existing_ip:
        raise HTTPException(status_code=400, detail="虚拟IP名称已存在")

    db_ip = VirtualIP(user_id=current_user.id, **ip.dict())
    db.add(db_ip)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="虚拟IP名称已存在")
    except Exception:
        db.rollback()
        raise

    db.refresh(db_ip)
    return {"success": True, "data": VirtualIPResponse.from_orm(db_ip)}


@router.get("/{ip_id}")
def get_virtual_ip(
    ip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ip = _get_owned_virtual_ip(db, current_user, ip_id)
    return {"success": True, "data": _detail_response(ip)}


def _detail_response(ip: VirtualIP) -> VirtualIPResponse:
    data = VirtualIPResponse.from_orm(ip)
    data.readiness = VirtualIPReadiness(**compute_virtual_ip_readiness(ip))
    return data


@router.get("/business/{ip_business_id}")
def get_virtual_ip_by_business_id(
    ip_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 获取虚拟 IP"""
    ip = _get_owned_virtual_ip(db, current_user, None, ip_business_id)
    return {"success": True, "data": _detail_response(ip)}


@router.put("/{ip_id}")
def update_virtual_ip(
    ip_id: int,
    ip_update: VirtualIPUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ip = _get_owned_virtual_ip(db, current_user, ip_id)

    updates = ip_update.dict(exclude_unset=True)
    if "name" in updates and updates["name"] != ip.name:
        existing_ip = (
            _not_deleted(db.query(VirtualIP), VirtualIP)
            .filter(VirtualIP.name == updates["name"])
            .first()
        )
        if existing_ip:
            raise HTTPException(status_code=400, detail="虚拟IP名称已存在")

    for k, v in updates.items():
        setattr(ip, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="虚拟IP名称已存在")
    except Exception:
        db.rollback()
        raise

    db.refresh(ip)
    return {"success": True, "data": VirtualIPResponse.from_orm(ip)}


@router.put("/business/{ip_business_id}")
def update_virtual_ip_by_business_id(
    ip_business_id: str,
    ip_update: VirtualIPUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 更新虚拟 IP"""
    ip = _get_owned_virtual_ip(db, current_user, None, ip_business_id)

    updates = ip_update.dict(exclude_unset=True)
    if "name" in updates and updates["name"] != ip.name:
        existing_ip = (
            _not_deleted(db.query(VirtualIP), VirtualIP)
            .filter(VirtualIP.name == updates["name"])
            .first()
        )
        if existing_ip:
            raise HTTPException(status_code=400, detail="虚拟IP名称已存在")

    for k, v in updates.items():
        setattr(ip, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="虚拟IP名称已存在")
    except Exception:
        db.rollback()
        raise

    db.refresh(ip)
    return {"success": True, "data": VirtualIPResponse.from_orm(ip)}


@router.delete("/{ip_id}")
def delete_virtual_ip(
    ip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ip = _get_owned_virtual_ip(db, current_user, ip_id)
    ip.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()
    return {"success": True, "message": "虚拟IP已删除"}


@router.delete("/business/{ip_business_id}")
def delete_virtual_ip_by_business_id(
    ip_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 删除虚拟 IP"""
    ip = _get_owned_virtual_ip(db, current_user, None, ip_business_id)
    ip.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()
    return {"success": True, "message": "虚拟IP已删除"}
