"""
迁移文件模板

创建时间: ${create_date}
版本: ${revision}
描述: ${message}
上级版本: ${down_revision | comma,n}

使用说明:
1. 在 upgrade() 函数中添加数据库升级逻辑
2. 在 downgrade() 函数中添加数据库降级逻辑
3. 使用 op.create_table() 创建表
4. 使用 op.add_column() 添加列
5. 使用 op.execute() 执行自定义SQL
6. 更多操作请参考: https://alembic.sqlalchemy.org/en/latest/ops.html
"""

# revision identifiers, used by Alembic.
revision = ${repr(revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

${imports if imports else ""}

def upgrade() -> None:
    """数据库升级操作"""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """数据库降级操作"""
    ${downgrades if downgrades else "pass"}


# 自定义工具函数
def table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """检查索引是否存在"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def create_table_if_not_exists(table_name: str, *args, **kwargs):
    """如果表不存在则创建"""
    if not table_exists(table_name):
        op.create_table(table_name, *args, **kwargs)


def add_column_if_not_exists(table_name: str, column):
    """如果列不存在则添加"""
    if not column_exists(table_name, column.name):
        op.add_column(table_name, column)


def create_index_if_not_exists(index_name: str, table_name: str, columns: list):
    """如果索引不存在则创建"""
    if not index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def execute_sql(sql: str, description: str = None):
    """执行SQL语句并记录日志"""
    if description:
        print(f"执行: {description}")
    try:
        op.execute(sql)
        print(f"✅ SQL执行成功: {sql[:50]}...")
    except Exception as e:
        print(f"❌ SQL执行失败: {e}")
        raise


def migrate_data(source_table: str, target_table: str, mapping: dict):
    """数据迁移工具"""
    bind = op.get_bind()

    # 构建映射SQL
    source_cols = ', '.join(mapping.keys())
    target_cols = ', '.join(mapping.values())

    sql = f"""
    INSERT INTO {target_table} ({target_cols})
    SELECT {source_cols} FROM {source_table}
    """

    try:
        result = bind.execute(sa.text(sql))
        print(f"✅ 数据迁移成功: {result.rowcount} 行")
    except Exception as e:
        print(f"❌ 数据迁移失败: {e}")
        raise
