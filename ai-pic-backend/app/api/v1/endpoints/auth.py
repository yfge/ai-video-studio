from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.core.middleware import (
    get_current_user_basic, 
    get_current_active_user, 
    record_user_login
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.user_management_service import UserManagementService

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册 - 默认创建未激活用户，需管理员审批"""
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
    
    # 创建新用户 - 默认未激活状态
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        language=user_data.language,
        timezone=user_data.timezone,
        # 默认值：未激活、未审批、邮箱未验证
        is_active=False,
        is_approved=False,
        email_verified=False,
        is_admin=False,
        is_superuser=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 生成邮箱验证令牌
    service = UserManagementService(db)
    activation_token = service.generate_activation_token(db_user.id)
    
    return db_user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    request: Request = None,
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 验证用户名和密码
    if not user or not verify_password(form_data.password, user.hashed_password):
        # 如果用户存在，增加失败登录次数
        if user:
            record_user_login(user, db, success=False)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查账户锁定状态
    if user.is_account_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="账户已被锁定，请稍后再试或联系管理员"
        )
    
    # 检查用户状态 - 这里只检查基础状态，详细检查在中间件中进行
    if not user.can_login:
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="请先验证邮箱后再登录"
            )
        elif not user.is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户待管理员审批，请耐心等待"
            )
        elif not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被停用，请联系管理员"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户状态异常，请联系管理员"
            )
    
    # 记录成功登录
    record_user_login(user, db, success=True)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息 - 需要通过审批的活跃用户"""
    return current_user

@router.post("/verify-email/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    """验证邮箱"""
    service = UserManagementService(db)
    user = service.verify_activation_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的验证令牌或令牌已过期"
        )
    
    return {"message": "邮箱验证成功", "user_id": user.id}

@router.post("/resend-verification/{user_id}")
def resend_verification_email(user_id: int, db: Session = Depends(get_db)):
    """重新发送验证邮件"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已经验证过了"
        )
    
    service = UserManagementService(db)
    activation_token = service.generate_activation_token(user_id)
    
    return {"message": "验证邮件已重新发送", "activation_token": activation_token} 