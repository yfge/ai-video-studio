from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, verify_token
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.types import JSON
from app.core.database import Base
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.virtual_ip import VirtualIP
from app.schemas.virtual_ip import VirtualIPCreate, VirtualIPUpdate, VirtualIPResponse

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建新用户
    from app.core.security import get_password_hash
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user 

class VirtualIPBase(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    background_story: Optional[str] = None

class VirtualIPCreate(VirtualIPBase):
    pass

class VirtualIPUpdate(VirtualIPBase):
    pass

class VirtualIPResponse(VirtualIPBase):
    id: int
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True 

@router.get("/ips", response_model=List[VirtualIPResponse])
def list_virtual_ips(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(VirtualIP).offset(skip).limit(limit).all()

@router.post("/ips", response_model=VirtualIPResponse)
def create_virtual_ip(ip: VirtualIPCreate, db: Session = Depends(get_db)):
    db_ip = VirtualIP(**ip.dict())
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return db_ip

@router.get("/ips/{ip_id}", response_model=VirtualIPResponse)
def get_virtual_ip(ip_id: int, db: Session = Depends(get_db)):
    ip = db.query(VirtualIP).filter(VirtualIP.id == ip_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    return ip

@router.put("/ips/{ip_id}", response_model=VirtualIPResponse)
def update_virtual_ip(ip_id: int, ip_update: VirtualIPUpdate, db: Session = Depends(get_db)):
    ip = db.query(VirtualIP).filter(VirtualIP.id == ip_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    for k, v in ip_update.dict(exclude_unset=True).items():
        setattr(ip, k, v)
    db.commit()
    db.refresh(ip)
    return ip

@router.delete("/ips/{ip_id}")
def delete_virtual_ip(ip_id: int, db: Session = Depends(get_db)):
    ip = db.query(VirtualIP).filter(VirtualIP.id == ip_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    db.delete(ip)
    db.commit()
    return {"message": "虚拟IP已删除"}

# 头像上传/AI生成接口可后续补充 