"""
数据种子文件: admin_user
创建时间: 2025-08-14 00:48:59
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import *

def seed_data():
    """执行数据种子"""
    db = SessionLocal()
    try:
        from app.core.security import get_password_hash
        
        # 检查admin用户是否已存在
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Admin用户已存在，跳过创建")
            return
        
        # 创建默认admin用户
        hashed_password = get_password_hash("Ai7dio")
        admin_user = User(
            username="admin",
            email="admin@ai-video-studio.com", 
            hashed_password=hashed_password,
            full_name="系统管理员",
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ 默认admin用户创建成功")
        print(f"   用户名: admin")
        print(f"   密码: Ai7dio")
        print(f"   邮箱: admin@ai-video-studio.com")
        
    except Exception as e:
        print(f"种子数据执行失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def rollback_data():
    """回滚种子数据"""
    db = SessionLocal()
    try:
        # 删除admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            db.delete(admin_user)
            db.commit()
            print("✅ Admin用户已删除")
        else:
            print("Admin用户不存在")
        
        print(f"种子数据 admin_user 回滚成功")
        
    except Exception as e:
        print(f"种子数据回滚失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
