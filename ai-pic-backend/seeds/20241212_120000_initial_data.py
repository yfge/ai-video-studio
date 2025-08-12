"""
初始数据种子
创建时间: 2024-12-12 12:00:00

这个种子创建系统的基础数据，包括:
1. 示例虚拟IP
2. 基础配置数据
3. 系统管理员用户（如果需要）
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.models.script import Story, Episode, Script
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
        logger.info("开始执行初始数据种子")
        
        # 创建示例虚拟IP
        virtual_ips_data = [
            {
                "name": "小雅",
                "description": "一个活泼可爱的年轻女孩，充满好奇心和冒险精神",
                "tags": ["年轻", "活泼", "女性", "现代"],
                "background_story": "小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。",
                "style_prompt": "年轻亚洲女性，22岁，长黑发，大眼睛，甜美笑容，现代时尚穿着，充满活力",
                "is_active": True,
                "is_public": True
            },
            {
                "name": "李教授",
                "description": "一位博学的中年教授，温和而富有智慧",
                "tags": ["中年", "教授", "男性", "知识分子"],
                "background_story": "李教授是一位45岁的大学教授，专门研究人工智能和机器学习。他为人温和，深受学生喜爱，经常在学术会议上发表演讲。他有一个幸福的家庭，业余时间喜欢阅读和园艺。",
                "style_prompt": "中年亚洲男性，45岁，戴眼镜，温和表情，学者气质，正装或休闲装",
                "is_active": True,
                "is_public": True
            },
            {
                "name": "奶奶陈",
                "description": "一位慈祥的老奶奶，充满人生智慧",
                "tags": ["老年", "奶奶", "女性", "慈祥"],
                "background_story": "陈奶奶今年70岁，是一位退休的小学老师。她有三个孙子孙女，非常疼爱他们。她喜欢做饭、织毛衣，经常给邻居的孩子们讲故事。她的人生阅历丰富，总是能给年轻人很好的建议。",
                "style_prompt": "亚洲老年女性，70岁，银白头发，慈祥笑容，传统或舒适穿着，温暖气质",
                "is_active": True,
                "is_public": True
            }
        ]
        
        created_count = 0
        for vip_data in virtual_ips_data:
            virtual_ip, created = get_or_create(
                db,
                VirtualIP,
                name=vip_data["name"],
                defaults=vip_data
            )
            
            if created:
                created_count += 1
                logger.info(f"创建虚拟IP: {virtual_ip.name}")
        
        logger.info(f"成功创建 {created_count} 个虚拟IP")
        
        # 创建示例故事
        stories_data = [
            {
                "title": "校园青春物语",
                "genre": "青春",
                "theme": "成长与友谊",
                "target_audience": "年轻人",
                "duration_minutes": 15,
                "premise": "讲述大学生活中的青春故事",
                "synopsis": "小雅在大学里遇到了各种有趣的人和事，在李教授的指导下成长，同时也从奶奶陈那里学到了人生智慧。",
                "main_conflict": "学业压力与个人理想的冲突",
                "resolution": "通过努力和身边人的帮助，找到了平衡点",
                "setting_time": "现代",
                "setting_location": "大学校园",
                "world_building": "现实主义风格的校园环境",
                "status": "draft",
                "is_public": True,
                "tags": ["校园", "青春", "成长"]
            }
        ]
        
        story_created_count = 0
        for story_data in stories_data:
            story, created = get_or_create(
                db,
                Story,
                title=story_data["title"],
                defaults=story_data
            )
            
            if created:
                story_created_count += 1
                logger.info(f"创建故事: {story.title}")
        
        logger.info(f"成功创建 {story_created_count} 个故事")
        
        db.commit()
        logger.info("初始数据种子执行成功")
        
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
        logger.info("开始回滚初始数据种子")
        
        # 删除创建的数据
        story_count = db.query(Story).filter(Story.title.in_(["校园青春物语"])).count()
        db.query(Story).filter(Story.title.in_(["校园青春物语"])).delete(synchronize_session=False)
        
        vip_count = db.query(VirtualIP).filter(VirtualIP.name.in_(["小雅", "李教授", "奶奶陈"])).count()
        db.query(VirtualIP).filter(VirtualIP.name.in_(["小雅", "李教授", "奶奶陈"])).delete(synchronize_session=False)
        
        db.commit()
        logger.info(f"回滚成功: 删除了 {vip_count} 个虚拟IP, {story_count} 个故事")
        
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
        # 检查必要的表是否存在
        tables_to_check = ["virtual_ips", "stories"]
        
        for table_name in tables_to_check:
            try:
                result = db.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
                result.fetchone()
            except Exception:
                logger.error(f"表 {table_name} 不存在或无法访问")
                return False
        
        logger.info("前置条件检查通过")
        return True
        
    except Exception as e:
        logger.error(f"前置条件检查失败: {e}")
        return False
    finally:
        db.close()

def get_seed_info():
    """获取种子信息"""
    return {
        "name": "initial_data",
        "description": "创建系统初始数据，包括示例虚拟IP和故事",
        "version": "1.0.0",
        "dependencies": [],
        "create_time": "2024-12-12 12:00:00"
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