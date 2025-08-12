"""
数据库迁移核心模块

提供与FastAPI架构一致的数据库迁移机制，扩展Alembic功能
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import importlib.util

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from alembic import command, script
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.environment import EnvironmentContext

from app.core.config import settings
from app.core.database import Base, engine

logger = logging.getLogger(__name__)

class MigrationError(Exception):
    """迁移异常"""
    pass

class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self, engine: Engine = None):
        self.engine = engine or create_engine(settings.DATABASE_URL)
        self.config = self._get_alembic_config()
        self.script_dir = ScriptDirectory.from_config(self.config)
        
    def _get_alembic_config(self) -> Config:
        """获取Alembic配置"""
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        alembic_ini_path = project_root / "alembic.ini"
        
        if not alembic_ini_path.exists():
            raise MigrationError(f"找不到alembic.ini文件: {alembic_ini_path}")
        
        config = Config(str(alembic_ini_path))
        config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        return config
    
    def get_current_revision(self) -> Optional[str]:
        """获取当前数据库版本"""
        try:
            with self.engine.connect() as conn:
                context = MigrationContext.configure(conn)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"获取当前版本失败: {e}")
            return None
    
    def get_head_revision(self) -> Optional[str]:
        """获取最新版本"""
        try:
            return self.script_dir.get_current_head()
        except Exception as e:
            logger.error(f"获取最新版本失败: {e}")
            return None
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """获取迁移历史"""
        history = []
        try:
            for revision in self.script_dir.walk_revisions():
                history.append({
                    'revision': revision.revision,
                    'down_revision': revision.down_revision,
                    'message': revision.doc,
                    'branch_labels': revision.branch_labels,
                    'depends_on': revision.depends_on,
                    'create_date': getattr(revision.module, 'create_date', None)
                })
        except Exception as e:
            logger.error(f"获取迁移历史失败: {e}")
        
        return history
    
    def check_migration_status(self) -> Dict[str, Any]:
        """检查迁移状态"""
        current = self.get_current_revision()
        head = self.get_head_revision()
        
        status = {
            'current_revision': current,
            'head_revision': head,
            'is_up_to_date': current == head,
            'needs_upgrade': current != head,
            'database_exists': self._check_database_exists()
        }
        
        if current and head:
            # 检查是否有未应用的迁移
            pending_migrations = self._get_pending_migrations(current, head)
            status['pending_migrations'] = pending_migrations
            status['pending_count'] = len(pending_migrations)
        
        return status
    
    def _check_database_exists(self) -> bool:
        """检查数据库是否存在"""
        try:
            with self.engine.connect() as conn:
                # 尝试执行简单查询
                conn.execute(text("SELECT 1"))
                return True
        except Exception:
            return False
    
    def _get_pending_migrations(self, current: str, head: str) -> List[str]:
        """获取待应用的迁移"""
        pending = []
        try:
            for revision in self.script_dir.walk_revisions(head, current):
                if revision.revision != current:
                    pending.append(revision.revision)
        except Exception as e:
            logger.error(f"获取待应用迁移失败: {e}")
        
        return pending
    
    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """创建新的迁移文件"""
        try:
            # 生成时间戳作为revision id的一部分
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if autogenerate:
                command.revision(
                    self.config, 
                    message=f"{timestamp}_{message}",
                    autogenerate=True
                )
            else:
                command.revision(
                    self.config,
                    message=f"{timestamp}_{message}"
                )
            
            logger.info(f"迁移文件创建成功: {message}")
            return self.get_head_revision()
            
        except Exception as e:
            logger.error(f"创建迁移失败: {e}")
            raise MigrationError(f"创建迁移失败: {e}")
    
    def upgrade(self, revision: str = "head") -> bool:
        """升级数据库"""
        try:
            logger.info(f"开始升级数据库到版本: {revision}")
            command.upgrade(self.config, revision)
            logger.info("数据库升级成功")
            return True
        except Exception as e:
            logger.error(f"数据库升级失败: {e}")
            raise MigrationError(f"数据库升级失败: {e}")
    
    def downgrade(self, revision: str) -> bool:
        """降级数据库"""
        try:
            logger.info(f"开始降级数据库到版本: {revision}")
            command.downgrade(self.config, revision)
            logger.info("数据库降级成功")
            return True
        except Exception as e:
            logger.error(f"数据库降级失败: {e}")
            raise MigrationError(f"数据库降级失败: {e}")
    
    def stamp(self, revision: str) -> bool:
        """标记数据库版本（不运行迁移）"""
        try:
            logger.info(f"标记数据库版本: {revision}")
            command.stamp(self.config, revision)
            logger.info("版本标记成功")
            return True
        except Exception as e:
            logger.error(f"版本标记失败: {e}")
            raise MigrationError(f"版本标记失败: {e}")
    
    def validate_migrations(self) -> Dict[str, Any]:
        """验证迁移文件的完整性"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 检查迁移文件语法
            for revision in self.script_dir.walk_revisions():
                try:
                    # 尝试导入迁移模块
                    spec = importlib.util.spec_from_file_location(
                        f"migration_{revision.revision}", 
                        revision.path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # 检查必需的函数
                        if not hasattr(module, 'upgrade'):
                            validation_result['errors'].append(
                                f"迁移 {revision.revision} 缺少 upgrade 函数"
                            )
                            validation_result['valid'] = False
                        
                        if not hasattr(module, 'downgrade'):
                            validation_result['warnings'].append(
                                f"迁移 {revision.revision} 缺少 downgrade 函数"
                            )
                            
                except Exception as e:
                    validation_result['errors'].append(
                        f"迁移 {revision.revision} 语法错误: {e}"
                    )
                    validation_result['valid'] = False
                    
        except Exception as e:
            validation_result['errors'].append(f"验证过程失败: {e}")
            validation_result['valid'] = False
        
        return validation_result
    
    def backup_before_migration(self) -> Optional[str]:
        """迁移前备份数据库（MySQL）"""
        if "mysql" not in settings.DATABASE_URL:
            logger.warning("当前数据库不是MySQL，跳过备份")
            return None
        
        try:
            import subprocess
            from urllib.parse import urlparse
            
            # 解析数据库URL
            parsed = urlparse(settings.DATABASE_URL.replace('mysql+pymysql://', 'mysql://'))
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backup_{timestamp}.sql"
            backup_path = Path(__file__).parent.parent.parent / "backups" / backup_file
            backup_path.parent.mkdir(exist_ok=True)
            
            # 构建mysqldump命令
            cmd = [
                "mysqldump",
                f"--host={parsed.hostname}",
                f"--port={parsed.port}",
                f"--user={parsed.username}",
                f"--password={parsed.password}",
                "--single-transaction",
                "--routines",
                "--triggers",
                parsed.path.lstrip('/')
            ]
            
            # 执行备份
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                logger.info(f"数据库备份成功: {backup_path}")
                return str(backup_path)
            else:
                logger.error(f"数据库备份失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"备份过程失败: {e}")
            return None
    
    def get_schema_diff(self) -> Dict[str, Any]:
        """获取当前数据库与模型的差异"""
        try:
            from alembic.autogenerate import compare_metadata
            
            with self.engine.connect() as conn:
                context = MigrationContext.configure(conn)
                diff = compare_metadata(context, Base.metadata)
                
                return {
                    'has_changes': len(diff) > 0,
                    'changes': [str(change) for change in diff],
                    'change_count': len(diff)
                }
                
        except Exception as e:
            logger.error(f"获取模式差异失败: {e}")
            return {'has_changes': False, 'error': str(e)}


class DataSeeder:
    """数据种子管理器"""
    
    def __init__(self, engine: Engine = None):
        self.engine = engine or create_engine(settings.DATABASE_URL)
        self.seeds_dir = Path(__file__).parent.parent.parent / "seeds"
        self.seeds_dir.mkdir(exist_ok=True)
    
    def create_seed_file(self, name: str) -> Path:
        """创建种子文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.py"
        seed_file = self.seeds_dir / filename
        
        template = '''"""
数据种子文件: {name}
创建时间: {create_time}
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import *

def seed_data():
    """执行数据种子"""
    db = SessionLocal()
    try:
        # TODO: 在这里添加种子数据
        
        # 示例:
        # user = User(username="admin", email="admin@example.com")
        # db.add(user)
        # db.commit()
        
        print(f"种子数据 {name} 执行成功")
        
    except Exception as e:
        print(f"种子数据执行失败: {{e}}")
        db.rollback()
        raise
    finally:
        db.close()

def rollback_data():
    """回滚种子数据"""
    db = SessionLocal()
    try:
        # TODO: 在这里添加回滚逻辑
        
        print(f"种子数据 {name} 回滚成功")
        
    except Exception as e:
        print(f"种子数据回滚失败: {{e}}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
'''.format(
            name=name,
            create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        seed_file.write_text(template, encoding='utf-8')
        logger.info(f"种子文件创建成功: {seed_file}")
        return seed_file
    
    def run_seed(self, seed_name: str) -> bool:
        """运行指定的种子"""
        try:
            seed_files = list(self.seeds_dir.glob(f"*{seed_name}.py"))
            if not seed_files:
                raise ValueError(f"找不到种子文件: {seed_name}")
            
            seed_file = seed_files[0]
            
            # 动态导入并执行种子
            spec = importlib.util.spec_from_file_location("seed_module", seed_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'seed_data'):
                    module.seed_data()
                    logger.info(f"种子 {seed_name} 执行成功")
                    return True
                else:
                    raise ValueError(f"种子文件 {seed_file} 缺少 seed_data 函数")
            else:
                raise ValueError(f"无法加载种子文件: {seed_file}")
                
        except Exception as e:
            logger.error(f"种子执行失败: {e}")
            raise
    
    def run_all_seeds(self) -> int:
        """运行所有种子"""
        seed_files = sorted(self.seeds_dir.glob("*.py"))
        success_count = 0
        
        for seed_file in seed_files:
            try:
                seed_name = seed_file.stem.split('_', 2)[-1]  # 提取种子名称
                self.run_seed(seed_name)
                success_count += 1
            except Exception as e:
                logger.error(f"种子 {seed_file.name} 执行失败: {e}")
                continue
        
        logger.info(f"成功执行 {success_count}/{len(seed_files)} 个种子")
        return success_count


# 全局实例
migration_manager = MigrationManager()
data_seeder = DataSeeder()