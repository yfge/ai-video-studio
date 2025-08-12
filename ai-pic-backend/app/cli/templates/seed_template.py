"""
数据种子模板: ${name}
创建时间: ${create_time}

这个模板提供了创建数据种子的基础结构。
请根据需要修改 seed_data() 和 rollback_data() 函数。

使用说明:
1. 在 seed_data() 中添加要插入的数据
2. 在 rollback_data() 中添加回滚逻辑
3. 使用 get_or_create() 避免重复插入
4. 使用事务确保数据一致性
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models import *
import logging

logger = logging.getLogger(__name__)

def get_or_create(db: Session, model, defaults=None, **kwargs):
    """获取或创建对象"""
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items())
        params.update(defaults or {})
        instance = model(**params)
        db.add(instance)
        return instance, True

def seed_data():
    """执行数据种子"""
    db = SessionLocal()
    try:
        logger.info("开始执行种子数据: ${name}")
        
        # TODO: 在这里添加种子数据逻辑
        
        # 示例: 创建管理员用户
        # admin_user, created = get_or_create(
        #     db, 
        #     User,
        #     username="admin",
        #     defaults={
        #         "email": "admin@example.com",
        #         "password": "hashed_password",
        #         "is_active": True,
        #         "is_superuser": True
        #     }
        # )
        # 
        # if created:
        #     logger.info("管理员用户创建成功")
        # else:
        #     logger.info("管理员用户已存在")
        
        # 示例: 创建虚拟IP
        # virtual_ip, created = get_or_create(
        #     db,
        #     VirtualIP,
        #     name="示例虚拟IP",
        #     defaults={
        #         "description": "这是一个示例虚拟IP",
        #         "tags": ["示例", "测试"],
        #         "background_story": "示例背景故事",
        #         "style_prompt": "示例风格提示",
        #         "is_active": True,
        #         "is_public": True
        #     }
        # )
        # 
        # if created:
        #     logger.info("示例虚拟IP创建成功")
        
        db.commit()
        logger.info(f"种子数据 ${name} 执行成功")
        
    except Exception as e:
        logger.error(f"种子数据执行失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def rollback_data():
    """回滚种子数据"""
    db = SessionLocal()
    try:
        logger.info("开始回滚种子数据: ${name}")
        
        # TODO: 在这里添加回滚逻辑
        
        # 示例: 删除创建的数据
        # db.query(User).filter_by(username="admin").delete()
        # db.query(VirtualIP).filter_by(name="示例虚拟IP").delete()
        
        db.commit()
        logger.info(f"种子数据 ${name} 回滚成功")
        
    except Exception as e:
        logger.error(f"种子数据回滚失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def check_prerequisites():
    """检查前置条件"""
    db = SessionLocal()
    try:
        # TODO: 检查种子执行前置条件
        
        # 示例: 检查表是否存在
        # result = db.execute(text("SHOW TABLES LIKE 'users'"))
        # if not result.fetchone():
        #     raise Exception("users表不存在，请先运行数据库迁移")
        
        return True
        
    except Exception as e:
        logger.error(f"前置条件检查失败: {e}")
        return False
    finally:
        db.close()

def get_seed_info():
    """获取种子信息"""
    return {
        "name": "${name}",
        "description": "种子数据描述",
        "version": "1.0.0",
        "dependencies": [],  # 依赖的其他种子
        "create_time": "${create_time}"
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_data()
    else:
        if check_prerequisites():
            seed_data()
        else:
            logger.error("前置条件检查失败，种子执行终止")