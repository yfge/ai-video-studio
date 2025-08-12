"""
迁移安全机制

提供数据库迁移的安全检查、回滚保护和数据完整性验证
"""

import os
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json

from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

class MigrationSafetyError(Exception):
    """迁移安全异常"""
    pass

class DataIntegrityChecker:
    """数据完整性检查器"""
    
    def __init__(self, engine: Engine = None):
        self.engine = engine or create_engine(settings.DATABASE_URL)
        
    def check_referential_integrity(self) -> Dict[str, Any]:
        """检查外键引用完整性"""
        result = {
            "valid": True,
            "violations": [],
            "warnings": []
        }
        
        try:
            inspector = inspect(self.engine)
            
            with self.engine.connect() as conn:
                for table_name in inspector.get_table_names():
                    foreign_keys = inspector.get_foreign_keys(table_name)
                    
                    for fk in foreign_keys:
                        # 检查外键约束
                        local_cols = ', '.join(fk['constrained_columns'])
                        ref_table = fk['referred_table']
                        ref_cols = ', '.join(fk['referred_columns'])
                        
                        query = f"""
                        SELECT COUNT(*) as violation_count
                        FROM {table_name} t1
                        LEFT JOIN {ref_table} t2 ON t1.{local_cols} = t2.{ref_cols}
                        WHERE t1.{local_cols} IS NOT NULL AND t2.{ref_cols} IS NULL
                        """
                        
                        try:
                            violation_result = conn.execute(text(query))
                            count = violation_result.fetchone()[0]
                            
                            if count > 0:
                                violation = {
                                    "table": table_name,
                                    "foreign_key": fk['name'],
                                    "violation_count": count,
                                    "description": f"表 {table_name} 有 {count} 行违反外键约束 {fk['name']}"
                                }
                                result["violations"].append(violation)
                                result["valid"] = False
                                
                        except Exception as e:
                            logger.warning(f"检查外键约束失败 {table_name}.{fk['name']}: {e}")
                            
        except Exception as e:
            result["valid"] = False
            result["error"] = str(e)
            logger.error(f"引用完整性检查失败: {e}")
        
        return result
    
    def check_data_consistency(self) -> Dict[str, Any]:
        """检查数据一致性"""
        result = {
            "valid": True,
            "inconsistencies": [],
            "statistics": {}
        }
        
        try:
            with self.engine.connect() as conn:
                # 检查基本数据统计
                inspector = inspect(self.engine)
                
                for table_name in inspector.get_table_names():
                    try:
                        # 获取行数
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_count = count_result.fetchone()[0]
                        
                        result["statistics"][table_name] = {
                            "row_count": row_count
                        }
                        
                        # 检查NULL值比例
                        columns = inspector.get_columns(table_name)
                        for column in columns:
                            if not column.get('nullable', True):  # 非空列
                                null_check = conn.execute(text(
                                    f"SELECT COUNT(*) FROM {table_name} WHERE {column['name']} IS NULL"
                                ))
                                null_count = null_check.fetchone()[0]
                                
                                if null_count > 0:
                                    inconsistency = {
                                        "table": table_name,
                                        "column": column['name'],
                                        "type": "null_in_not_null_column",
                                        "count": null_count,
                                        "description": f"非空列 {table_name}.{column['name']} 包含 {null_count} 个NULL值"
                                    }
                                    result["inconsistencies"].append(inconsistency)
                                    result["valid"] = False
                                    
                    except Exception as e:
                        logger.warning(f"检查表 {table_name} 一致性失败: {e}")
                        
        except Exception as e:
            result["valid"] = False
            result["error"] = str(e)
            logger.error(f"数据一致性检查失败: {e}")
        
        return result
    
    def generate_data_fingerprint(self) -> str:
        """生成数据指纹用于变更检测"""
        try:
            fingerprint_data = {}
            
            with self.engine.connect() as conn:
                inspector = inspect(self.engine)
                
                for table_name in inspector.get_table_names():
                    try:
                        # 获取表的行数和校验和
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_count = count_result.fetchone()[0]
                        
                        # 对于MySQL，可以使用CHECKSUM TABLE
                        if "mysql" in settings.DATABASE_URL:
                            checksum_result = conn.execute(text(f"CHECKSUM TABLE {table_name}"))
                            checksum = checksum_result.fetchone()[1]
                        else:
                            # 对于其他数据库，使用行数作为简单校验
                            checksum = row_count
                        
                        fingerprint_data[table_name] = {
                            "row_count": row_count,
                            "checksum": checksum
                        }
                        
                    except Exception as e:
                        logger.warning(f"生成表 {table_name} 指纹失败: {e}")
                        fingerprint_data[table_name] = {"error": str(e)}
            
            # 生成MD5哈希
            fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
            return hashlib.md5(fingerprint_str.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"生成数据指纹失败: {e}")
            return f"error_{datetime.now().timestamp()}"

class MigrationRollbackManager:
    """迁移回滚管理器"""
    
    def __init__(self, engine: Engine = None):
        self.engine = engine or create_engine(settings.DATABASE_URL)
        self.rollback_dir = Path(__file__).parent.parent.parent / "rollbacks"
        self.rollback_dir.mkdir(exist_ok=True)
        
    def create_rollback_point(self, migration_id: str, description: str = "") -> str:
        """创建回滚点"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rollback_id = f"{timestamp}_{migration_id}"
            
            rollback_info = {
                "rollback_id": rollback_id,
                "migration_id": migration_id,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "database_url": settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else "local",
                "schema_snapshot": self._capture_schema_snapshot(),
                "data_fingerprint": DataIntegrityChecker(self.engine).generate_data_fingerprint()
            }
            
            # 保存回滚信息
            rollback_file = self.rollback_dir / f"{rollback_id}.json"
            with open(rollback_file, 'w', encoding='utf-8') as f:
                json.dump(rollback_info, f, indent=2, ensure_ascii=False)
            
            # 创建数据备份（如果是MySQL）
            if "mysql" in settings.DATABASE_URL:
                backup_file = self._create_data_backup(rollback_id)
                rollback_info["backup_file"] = backup_file
                
                # 更新回滚信息文件
                with open(rollback_file, 'w', encoding='utf-8') as f:
                    json.dump(rollback_info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"回滚点创建成功: {rollback_id}")
            return rollback_id
            
        except Exception as e:
            logger.error(f"创建回滚点失败: {e}")
            raise MigrationSafetyError(f"创建回滚点失败: {e}")
    
    def _capture_schema_snapshot(self) -> Dict[str, Any]:
        """捕获数据库架构快照"""
        try:
            inspector = inspect(self.engine)
            schema_snapshot = {
                "tables": {},
                "indexes": {},
                "foreign_keys": {}
            }
            
            for table_name in inspector.get_table_names():
                # 表结构
                columns = inspector.get_columns(table_name)
                schema_snapshot["tables"][table_name] = {
                    "columns": [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col.get("nullable", True),
                            "default": str(col.get("default")) if col.get("default") else None
                        }
                        for col in columns
                    ]
                }
                
                # 索引
                indexes = inspector.get_indexes(table_name)
                schema_snapshot["indexes"][table_name] = [
                    {
                        "name": idx["name"],
                        "columns": idx["column_names"],
                        "unique": idx.get("unique", False)
                    }
                    for idx in indexes
                ]
                
                # 外键
                foreign_keys = inspector.get_foreign_keys(table_name)
                schema_snapshot["foreign_keys"][table_name] = [
                    {
                        "name": fk["name"],
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"]
                    }
                    for fk in foreign_keys
                ]
            
            return schema_snapshot
            
        except Exception as e:
            logger.error(f"捕获架构快照失败: {e}")
            return {"error": str(e)}
    
    def _create_data_backup(self, rollback_id: str) -> Optional[str]:
        """创建数据备份"""
        try:
            import subprocess
            from urllib.parse import urlparse
            
            # 解析数据库URL
            parsed = urlparse(settings.DATABASE_URL.replace('mysql+pymysql://', 'mysql://'))
            
            # 生成备份文件名
            backup_file = f"rollback_{rollback_id}.sql"
            backup_path = self.rollback_dir / backup_file
            
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
                "--add-drop-table",
                parsed.path.lstrip('/')
            ]
            
            # 执行备份
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                logger.info(f"数据备份成功: {backup_path}")
                return str(backup_file)
            else:
                logger.error(f"数据备份失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"创建数据备份失败: {e}")
            return None
    
    def list_rollback_points(self) -> List[Dict[str, Any]]:
        """列出所有回滚点"""
        rollback_points = []
        
        try:
            for rollback_file in self.rollback_dir.glob("*.json"):
                try:
                    with open(rollback_file, 'r', encoding='utf-8') as f:
                        rollback_info = json.load(f)
                    
                    # 添加文件信息
                    rollback_info["file_path"] = str(rollback_file)
                    rollback_info["file_size"] = rollback_file.stat().st_size
                    
                    rollback_points.append(rollback_info)
                    
                except Exception as e:
                    logger.warning(f"读取回滚点文件失败 {rollback_file}: {e}")
            
            # 按创建时间排序
            rollback_points.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
        except Exception as e:
            logger.error(f"列出回滚点失败: {e}")
        
        return rollback_points
    
    def cleanup_old_rollbacks(self, keep_days: int = 30):
        """清理过期的回滚点"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            cleaned_count = 0
            
            for rollback_file in self.rollback_dir.glob("*.json"):
                try:
                    with open(rollback_file, 'r', encoding='utf-8') as f:
                        rollback_info = json.load(f)
                    
                    created_at = datetime.fromisoformat(rollback_info["created_at"])
                    
                    if created_at < cutoff_date:
                        # 删除回滚文件
                        rollback_file.unlink()
                        
                        # 删除相关的备份文件
                        backup_file = rollback_info.get("backup_file")
                        if backup_file:
                            backup_path = self.rollback_dir / backup_file
                            if backup_path.exists():
                                backup_path.unlink()
                        
                        cleaned_count += 1
                        logger.info(f"删除过期回滚点: {rollback_info['rollback_id']}")
                        
                except Exception as e:
                    logger.warning(f"清理回滚点失败 {rollback_file}: {e}")
            
            logger.info(f"清理完成，删除了 {cleaned_count} 个过期回滚点")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理回滚点失败: {e}")
            return 0

class MigrationValidator:
    """迁移验证器"""
    
    def __init__(self, engine: Engine = None):
        self.engine = engine or create_engine(settings.DATABASE_URL)
        self.integrity_checker = DataIntegrityChecker(self.engine)
        
    def pre_migration_check(self) -> Dict[str, Any]:
        """迁移前检查"""
        result = {
            "safe_to_migrate": True,
            "warnings": [],
            "errors": [],
            "checks": {}
        }
        
        try:
            # 检查数据库连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            result["checks"]["database_connection"] = True
            
            # 检查数据完整性
            integrity_result = self.integrity_checker.check_referential_integrity()
            result["checks"]["referential_integrity"] = integrity_result["valid"]
            
            if not integrity_result["valid"]:
                result["safe_to_migrate"] = False
                for violation in integrity_result["violations"]:
                    result["errors"].append(f"外键约束违反: {violation['description']}")
            
            # 检查数据一致性
            consistency_result = self.integrity_checker.check_data_consistency()
            result["checks"]["data_consistency"] = consistency_result["valid"]
            
            if not consistency_result["valid"]:
                result["safe_to_migrate"] = False
                for inconsistency in consistency_result["inconsistencies"]:
                    result["errors"].append(f"数据不一致: {inconsistency['description']}")
            
            # 检查磁盘空间（如果可能）
            try:
                import shutil
                total, used, free = shutil.disk_usage(Path(__file__).parent)
                free_gb = free // (1024**3)
                
                if free_gb < 1:  # 少于1GB
                    result["warnings"].append(f"磁盘空间不足: 仅剩 {free_gb}GB")
                
                result["checks"]["disk_space"] = free_gb
                
            except Exception:
                result["warnings"].append("无法检查磁盘空间")
            
            # 检查表锁定状态
            if "mysql" in settings.DATABASE_URL:
                try:
                    with self.engine.connect() as conn:
                        lock_result = conn.execute(text("SHOW OPEN TABLES WHERE In_use > 0"))
                        locked_tables = lock_result.fetchall()
                        
                        if locked_tables:
                            result["warnings"].append(f"发现 {len(locked_tables)} 个锁定的表")
                            
                        result["checks"]["table_locks"] = len(locked_tables) == 0
                        
                except Exception as e:
                    result["warnings"].append(f"无法检查表锁定状态: {e}")
            
        except Exception as e:
            result["safe_to_migrate"] = False
            result["errors"].append(f"迁移前检查失败: {e}")
            logger.error(f"迁移前检查失败: {e}")
        
        return result
    
    def post_migration_check(self, pre_migration_fingerprint: str) -> Dict[str, Any]:
        """迁移后检查"""
        result = {
            "migration_successful": True,
            "warnings": [],
            "errors": [],
            "checks": {}
        }
        
        try:
            # 重新检查数据完整性
            integrity_result = self.integrity_checker.check_referential_integrity()
            result["checks"]["referential_integrity"] = integrity_result["valid"]
            
            if not integrity_result["valid"]:
                result["migration_successful"] = False
                for violation in integrity_result["violations"]:
                    result["errors"].append(f"迁移后外键约束违反: {violation['description']}")
            
            # 检查数据一致性
            consistency_result = self.integrity_checker.check_data_consistency()
            result["checks"]["data_consistency"] = consistency_result["valid"]
            
            if not consistency_result["valid"]:
                for inconsistency in consistency_result["inconsistencies"]:
                    result["warnings"].append(f"迁移后数据不一致: {inconsistency['description']}")
            
            # 比较数据指纹
            post_migration_fingerprint = self.integrity_checker.generate_data_fingerprint()
            result["checks"]["data_fingerprint_changed"] = pre_migration_fingerprint != post_migration_fingerprint
            
            if pre_migration_fingerprint == post_migration_fingerprint:
                result["warnings"].append("数据指纹未变化，迁移可能未生效")
            
            result["pre_migration_fingerprint"] = pre_migration_fingerprint
            result["post_migration_fingerprint"] = post_migration_fingerprint
            
        except Exception as e:
            result["migration_successful"] = False
            result["errors"].append(f"迁移后检查失败: {e}")
            logger.error(f"迁移后检查失败: {e}")
        
        return result

# 全局实例
migration_validator = MigrationValidator()
rollback_manager = MigrationRollbackManager()
integrity_checker = DataIntegrityChecker()