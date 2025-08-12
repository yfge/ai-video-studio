# AI Video Studio 数据库迁移系统指南

本项目实现了一个与FastAPI架构深度集成的数据库迁移系统，扩展了Alembic功能，提供了更强大的迁移管理、数据种子、安全检查和API接口。

## 系统特性

### 🚀 核心功能
- **扩展Alembic**: 在Alembic基础上增加了更多高级功能
- **Django风格管理**: 提供类似Django的`manage.py`命令行接口
- **FastAPI集成**: 完全集成到FastAPI架构中
- **数据种子系统**: 内置数据种子管理机制
- **安全检查**: 迁移前后的完整性验证
- **回滚保护**: 自动备份和回滚点管理
- **API接口**: 通过REST API管理迁移状态
- **实时监控**: 中间件级别的迁移状态监控

### 🛡️ 安全特性
- **数据完整性检查**: 外键约束和数据一致性验证
- **自动备份**: MySQL数据库迁移前自动备份
- **回滚点管理**: 创建和管理迁移回滚点
- **迁移验证**: 迁移文件语法和完整性检查
- **模式差异检测**: 检测未提交的模式变更

## 系统架构

```
app/
├── core/
│   ├── migrations.py          # 核心迁移管理器
│   ├── migration_safety.py    # 安全检查和回滚管理
│   └── database.py           # 数据库配置
├── cli/
│   ├── migration_commands.py  # CLI命令实现
│   └── templates/            # 迁移和种子模板
├── api/v1/endpoints/
│   └── migrations.py         # REST API端点
├── middleware/
│   └── migration_middleware.py # 迁移状态监控中间件
└── tests/
    ├── test_migrations.py     # Alembic迁移测试
    └── test_migration_system.py # 自定义系统测试
```

## 快速开始

### 1. 安装依赖

```bash
cd ai-pic-backend
pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `.env` 文件：

```bash
# MySQL配置（推荐）
DATABASE_URL=mysql+pymysql://root:Pa88word@127.0.0.1:13306/ai_video_studio?charset=utf8mb4

# 或SQLite配置（开发环境）
# DATABASE_URL=sqlite:///./ai_pic.db
```

### 3. 初始化数据库

```bash
# 使用管理脚本（推荐）
python manage.py migration init
python manage.py migration upgrade

# 或使用MySQL专用脚本
python migrate_mysql.py init
python migrate_mysql.py upgrade
```

### 4. 验证迁移

```bash
# 检查迁移状态
python manage.py migration status

# 验证迁移文件
python manage.py migration validate
```

## 命令行接口

### Django风格管理命令

```bash
# 查看所有可用命令
python manage.py

# 迁移管理
python manage.py migration create -m "添加新字段"
python manage.py migration upgrade
python manage.py migration downgrade -r <版本>
python manage.py migration status
python manage.py migration history
python manage.py migration validate

# 数据种子管理
python manage.py seed create -n "initial_data"
python manage.py seed run -n "initial_data"
python manage.py seed run --all

# 服务器管理
python manage.py server run --host 0.0.0.0 --port 8000
python manage.py server production --workers 4

# 开发工具
python manage.py dev check          # 项目配置检查
python manage.py dev test           # 运行测试
python manage.py dev lint           # 代码质量检查
python manage.py dev format         # 代码格式化
python manage.py dev shell          # 交互式Shell

# 快速启动
python manage.py quickstart         # 一键启动项目
```

### 专用迁移命令

```bash
# MySQL专用命令
python migrate_mysql.py init        # 初始化数据库
python migrate_mysql.py create -m "消息"
python migrate_mysql.py upgrade
python migrate_mysql.py test        # 测试连接
python migrate_mysql.py migrate     # 从SQLite迁移数据

# 传统CLI命令
python app/cli/migration_commands.py migration status
python app/cli/migration_commands.py seed run --all
```

## API接口

### 迁移状态API

```bash
# 获取迁移状态
GET /api/v1/migrations/status

# 获取迁移历史
GET /api/v1/migrations/history

# 验证迁移文件
GET /api/v1/migrations/validate

# 获取模式差异
GET /api/v1/migrations/schema-diff

# 系统健康检查
GET /api/v1/migrations/health

# 获取系统信息
GET /api/v1/migrations/info
```

### 迁移管理API

```bash
# 升级数据库（后台任务）
POST /api/v1/migrations/upgrade
{
  "revision": "head",
  "backup": true
}

# 创建迁移
POST /api/v1/migrations/create-migration
{
  "message": "添加新功能",
  "autogenerate": true
}

# 标记版本
POST /api/v1/migrations/stamp
{
  "revision": "abc123"
}

# 运行数据种子
POST /api/v1/migrations/seeds/run
{
  "seed_name": "initial_data",
  "run_all": false
}
```

### API响应示例

```json
{
  "current_revision": "abc123def456",
  "head_revision": "def456ghi789",
  "is_up_to_date": false,
  "needs_upgrade": true,
  "database_exists": true,
  "pending_migrations": ["def456ghi789"],
  "pending_count": 1
}
```

## 数据种子系统

### 创建种子文件

```bash
# 创建新种子
python manage.py seed create -n "initial_users"
```

自动生成的种子文件模板：

```python
"""
数据种子文件: initial_users
创建时间: 2024-12-12 12:00:00
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import *

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
        # 添加种子数据逻辑
        admin_user, created = get_or_create(
            db, 
            User,
            username="admin",
            defaults={
                "email": "admin@example.com",
                "hashed_password": "hashed_password",
                "is_active": True,
                "is_superuser": True
            }
        )
        
        db.commit()
        print("种子数据执行成功")
        
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
        # 添加回滚逻辑
        db.query(User).filter_by(username="admin").delete()
        db.commit()
        print("种子数据回滚成功")
        
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
```

### 运行种子

```bash
# 运行特定种子
python manage.py seed run -n "initial_users"

# 运行所有种子
python manage.py seed run --all

# 通过API运行
curl -X POST "http://localhost:8000/api/v1/migrations/seeds/run" \
  -H "Content-Type: application/json" \
  -d '{"seed_name": "initial_users"}'
```

## 安全检查系统

### 迁移前检查

系统会自动执行以下检查：

1. **数据库连接**: 验证数据库连接可用
2. **引用完整性**: 检查外键约束
3. **数据一致性**: 验证数据完整性
4. **磁盘空间**: 检查可用存储空间
5. **表锁定**: 检查是否有表被锁定
6. **迁移文件验证**: 检查迁移文件语法

### 迁移后验证

1. **完整性重检**: 重新验证数据完整性
2. **数据指纹对比**: 检测数据变化
3. **模式验证**: 确认模式应用正确

### 回滚点管理

```bash
# 创建回滚点
rollback_id = rollback_manager.create_rollback_point(
    migration_id="add_user_table",
    description="添加用户表前的备份"
)

# 列出回滚点
rollback_points = rollback_manager.list_rollback_points()

# 清理过期回滚点
cleaned_count = rollback_manager.cleanup_old_rollbacks(keep_days=30)
```

## 中间件集成

### 自动迁移检查

在FastAPI应用中集成迁移检查中间件：

```python
from app.middleware import MigrationCheckMiddleware, DatabaseHealthMiddleware

# 添加到FastAPI应用
app.add_middleware(
    MigrationCheckMiddleware,
    check_on_startup=True,
    require_up_to_date=False  # 生产环境可设为True
)

app.add_middleware(
    DatabaseHealthMiddleware,
    health_check_interval=300  # 5分钟检查一次
)
```

中间件功能：
- **启动时检查**: 应用启动时自动检查迁移状态
- **响应头注入**: 在HTTP响应中添加迁移状态信息
- **服务保护**: 可配置在数据库未升级时阻止访问
- **健康监控**: 定期检查数据库连接健康状态

## 迁移模板系统

### 自定义迁移模板

系统提供了增强的迁移模板，包含更多工具函数：

```python
"""
迁移文件模板
版本: ${revision}
描述: ${message}
"""

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    """数据库升级操作"""
    # 安全创建表
    create_table_if_not_exists('new_table',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False)
    )
    
    # 安全添加列
    add_column_if_not_exists('existing_table', 
        sa.Column('new_column', sa.String(50))
    )
    
    # 安全创建索引
    create_index_if_not_exists('idx_name', 'table_name', ['column1', 'column2'])

def downgrade() -> None:
    """数据库降级操作"""
    op.drop_table('new_table')
```

### 工具函数

模板提供了以下安全工具函数：

- `table_exists(table_name)`: 检查表是否存在
- `column_exists(table_name, column_name)`: 检查列是否存在
- `index_exists(table_name, index_name)`: 检查索引是否存在
- `create_table_if_not_exists()`: 安全创建表
- `add_column_if_not_exists()`: 安全添加列
- `create_index_if_not_exists()`: 安全创建索引
- `execute_sql()`: 执行SQL并记录日志
- `migrate_data()`: 数据迁移工具

## 测试系统

### 运行迁移测试

```bash
# 运行所有迁移相关测试
python -m pytest tests/test_migration_system.py -v

# 运行Alembic迁移测试
python -m pytest tests/test_migrations.py -v

# 运行特定测试
python -m pytest tests/test_migration_system.py::TestMigrationManager -v
```

### 测试覆盖

测试系统覆盖以下功能：

1. **迁移管理器测试**: 创建、升级、降级、状态检查
2. **数据种子测试**: 种子文件创建和执行
3. **完整性检查测试**: 数据完整性和引用完整性
4. **回滚管理测试**: 回滚点创建和清理
5. **安全检查测试**: 迁移前后验证
6. **集成测试**: 完整工作流测试

## 生产环境部署

### 生产环境配置

1. **启用中间件保护**:
```python
app.add_middleware(
    MigrationCheckMiddleware,
    require_up_to_date=True  # 强制要求数据库最新
)
```

2. **配置自动备份**:
```bash
# 设置备份目录权限
mkdir -p /var/backups/ai-video-studio
chown app:app /var/backups/ai-video-studio

# 配置定期清理
echo "0 2 * * 0 /usr/local/bin/cleanup-rollbacks.sh" | crontab -
```

3. **监控迁移状态**:
```bash
# 健康检查端点
curl http://localhost:8000/api/v1/migrations/health

# 监控脚本
#!/bin/bash
STATUS=$(curl -s http://localhost:8000/api/v1/migrations/status | jq -r '.is_up_to_date')
if [ "$STATUS" != "true" ]; then
    echo "⚠️ 数据库需要升级" | mail -s "Migration Alert" admin@example.com
fi
```

### 部署工作流

```bash
# 1. 部署代码
git pull origin main

# 2. 检查迁移状态
python manage.py migration status

# 3. 创建备份
python manage.py migration validate
python migrate_mysql.py test

# 4. 执行迁移
python manage.py migration upgrade --backup

# 5. 运行种子（如果需要）
python manage.py seed run --all

# 6. 验证部署
python manage.py dev check
```

## 故障排除

### 常见问题

**1. 迁移文件冲突**
```bash
# 查看迁移历史
python manage.py migration history

# 合并分支迁移
python manage.py migration merge
```

**2. 数据完整性问题**
```bash
# 检查数据完整性
python manage.py migration validate

# 修复外键约束
python manage.py migration check-integrity
```

**3. 回滚到安全点**
```bash
# 列出回滚点
python manage.py migration rollback-points

# 执行回滚
python manage.py migration rollback <rollback_id>
```

**4. 种子执行失败**
```bash
# 检查种子前置条件
python seeds/xxx_seed.py

# 手动回滚种子
python seeds/xxx_seed.py rollback
```

### 日志调试

启用详细日志：

```python
import logging
logging.getLogger('app.core.migrations').setLevel(logging.DEBUG)
logging.getLogger('alembic').setLevel(logging.INFO)
```

## 最佳实践

### 迁移开发

1. **总是先备份**: 生产环境迁移前创建完整备份
2. **渐进式迁移**: 大型迁移分解为多个小步骤
3. **可逆操作**: 确保每个迁移都有对应的回滚操作
4. **测试驱动**: 在测试环境充分验证迁移
5. **文档记录**: 为复杂迁移编写详细说明

### 数据种子

1. **幂等性**: 种子可以重复运行而不产生副作用
2. **依赖管理**: 明确种子之间的依赖关系
3. **环境区分**: 为不同环境准备不同的种子数据
4. **版本控制**: 种子文件纳入版本控制

### 安全考虑

1. **权限控制**: 限制迁移API的访问权限
2. **审计日志**: 记录所有迁移操作
3. **监控告警**: 配置迁移状态监控
4. **容灾准备**: 准备迁移失败的恢复方案

## 扩展开发

### 添加新的检查器

```python
class CustomIntegrityChecker:
    def check_business_rules(self) -> Dict[str, Any]:
        """检查业务规则完整性"""
        # 实现自定义检查逻辑
        pass

# 集成到验证器
validator = MigrationValidator()
validator.custom_checkers.append(CustomIntegrityChecker())
```

### 自定义迁移命令

```python
@migration.command()
@click.option('--dry-run', is_flag=True, help='仅显示将要执行的操作')
def custom_migrate(dry_run):
    """自定义迁移命令"""
    if dry_run:
        click.echo("将要执行的迁移操作...")
    else:
        # 执行实际迁移
        pass
```

### 添加新的API端点

```python
@router.post("/custom-operation")
async def custom_migration_operation():
    """自定义迁移操作端点"""
    # 实现自定义逻辑
    return {"status": "success"}
```

## 更新日志

### v2.0.0 (当前版本)
- ✨ 全新的迁移系统架构
- 🛡️ 增强的安全检查机制
- 🌱 完整的数据种子系统
- 🔧 Django风格的管理命令
- 📡 REST API接口
- 🧪 全面的测试覆盖

### 未来计划
- 🔄 自动迁移调度
- 📊 迁移性能分析
- 🌐 分布式迁移支持
- 📱 移动端管理界面

---

**注意**: 本迁移系统专为AI Video Studio项目设计，与FastAPI架构深度集成。在使用前请确保充分理解各项功能，并在测试环境中验证所有操作。