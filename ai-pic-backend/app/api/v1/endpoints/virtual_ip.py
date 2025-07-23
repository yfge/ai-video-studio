from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.virtual_ip import VirtualIP
from app.schemas.virtual_ip import VirtualIPCreate, VirtualIPUpdate, VirtualIPResponse

router = APIRouter()

@router.get("/", response_model=List[VirtualIPResponse])
def list_virtual_ips(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(VirtualIP).offset(skip).limit(limit).all()

@router.post("/", response_model=VirtualIPResponse)
def create_virtual_ip(ip: VirtualIPCreate, db: Session = Depends(get_db)):
    db_ip = VirtualIP(**ip.dict())
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return db_ip

@router.get("/{ip_id}", response_model=VirtualIPResponse)
def get_virtual_ip(ip_id: int, db: Session = Depends(get_db)):
    ip = db.query(VirtualIP).filter(VirtualIP.id == ip_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    return ip

@router.put("/{ip_id}", response_model=VirtualIPResponse)
def update_virtual_ip(ip_id: int, ip_update: VirtualIPUpdate, db: Session = Depends(get_db)):
    ip = db.query(VirtualIP).filter(VirtualIP.id == ip_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    for k, v in ip_update.dict(exclude_unset=True).items():
        setattr(ip, k, v)
    db.commit()
    db.refresh(ip)
    return ip

@router.delete("/{ip_id}")
def delete_virtual_ip(ip_id: int, db: Session = Depends(get_db)):
    ip = db.query(VirtualIP).filter(VirtualIP.id == ip_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    db.delete(ip)
    db.commit()
    return {"message": "虚拟IP已删除"} 