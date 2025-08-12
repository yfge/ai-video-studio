# MySQL数据库配置指南

本指南介绍如何为AI短剧制作平台配置MySQL数据库。

## 数据库配置信息

```bash
Host: 127.0.0.1
Port: 13306
Username: root
Password: Pa88word
Database: ai_video_studio
```

## 快速开始

### 1. 安装依赖

```bash
cd ai-pic-backend
pip install -r requirements.txt
```

新增的MySQL相关依赖：
- `pymysql==1.1.0` - MySQL Python客户端
- `cryptography==41.0.8` - PyMySQL加密支持

### 2. 环境配置

复制并配置环境变量：

```bash
cp env.example .env
```

编辑 `.env` 文件，确保数据库配置正确：

```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://root:Pa88word@127.0.0.1:13306/ai_video_studio?charset=utf8mb4
```

### 3. 数据库初始化

#### 方法一：使用初始化脚本（推荐）

```bash
# 创建数据库并测试连接
python scripts/init_mysql_db.py
```

#### 方法二：手动创建数据库

连接到MySQL服务器并创建数据库：

```sql
CREATE DATABASE ai_video_studio 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

### 4. 运行数据库迁移

#### 使用迁移管理脚本（推荐）

```bash
# 初始化数据库和运行迁移
python migrate_mysql.py init
python migrate_mysql.py upgrade
```

#### 使用Alembic直接操作

```bash
# 升级到最新版本
alembic upgrade head

# 查看当前版本
alembic current
```

### 5. 测试连接

```bash
# 运行连接测试
python test_mysql_connection.py
```

## 数据库迁移管理

### 迁移管理脚本

项目提供了 `migrate_mysql.py` 脚本来管理数据库迁移：

```bash
# 初始化数据库
python migrate_mysql.py init

# 创建新迁移
python migrate_mysql.py create -m "添加新功能"

# 升级数据库
python migrate_mysql.py upgrade

# 降级数据库
python migrate_mysql.py downgrade -r <版本号>

# 查看当前版本
python migrate_mysql.py current

# 查看迁移历史
python migrate_mysql.py history

# 测试数据库连接
python migrate_mysql.py test

# 重置数据库（危险操作）
python migrate_mysql.py reset
```

### 从SQLite迁移数据

如果你之前使用SQLite数据库，可以使用迁移脚本：

```bash
# 迁移现有SQLite数据到MySQL
python scripts/migrate_to_mysql.py
```

### 手动Alembic操作

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述信息"

# 升级到最新版本
alembic upgrade head

# 降级到指定版本
alembic downgrade <版本号>

# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 查看迁移头
alembic heads
```

## 数据库配置详解

### 连接池配置

MySQL连接池配置（在 `app/core/database.py` 中）：

```python
"pool_size": 20,           # 连接池大小
"max_overflow": 0,         # 最大溢出连接数
"pool_pre_ping": True,     # 连接前ping测试
"pool_recycle": 3600,      # 连接回收时间（秒）
```

### 字符集配置

```python
"connect_args": {
    "charset": "utf8mb4",  # 字符集，支持emoji
    "autocommit": False    # 关闭自动提交
}
```

## 环境变量配置

### 开发环境

```bash
# SQLite（轻量级开发）
DATABASE_URL=sqlite:///./ai_pic.db

# MySQL（推荐）
DATABASE_URL=mysql+pymysql://root:Pa88word@127.0.0.1:13306/ai_video_studio?charset=utf8mb4
```

### 生产环境

```bash
# MySQL生产环境
DATABASE_URL=mysql+pymysql://username:password@host:port/database?charset=utf8mb4

# 其他数据库配置
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=["https://yourdomain.com"]
```

## 常见问题解决

### 1. 连接被拒绝

```bash
Error: (2003, "Can't connect to MySQL server on '127.0.0.1:13306'")
```

**解决方案：**
- 确认MySQL服务正在运行
- 检查端口号是否正确（13306）
- 验证防火墙设置

### 2. 认证失败

```bash
Error: (1045, "Access denied for user 'root'@'localhost'")
```

**解决方案：**
- 检查用户名和密码是否正确
- 确认MySQL用户权限设置
- 检查MySQL的认证插件配置

### 3. 数据库不存在

```bash
Error: (1049, "Unknown database 'ai_video_studio'")
```

**解决方案：**
```bash
# 运行数据库初始化脚本
python scripts/init_mysql_db.py
```

### 4. 字符集问题

如果遇到中文字符插入问题，确认：

1. 数据库字符集为 `utf8mb4`
2. 连接URL包含 `charset=utf8mb4`
3. MySQL配置支持 `utf8mb4`

### 5. 迁移冲突

```bash
Error: Target database is not up to date
```

**解决方案：**
```bash
# 查看当前状态
python migrate_mysql.py current

# 查看迁移历史
python migrate_mysql.py history

# 手动解决冲突或重置
python migrate_mysql.py reset
```

## 性能优化建议

### 1. 索引优化

确保为常用查询字段创建索引：

```sql
-- 虚拟IP查询索引
CREATE INDEX idx_virtual_ip_name ON virtual_ips(name);
CREATE INDEX idx_virtual_ip_is_active ON virtual_ips(is_active);

-- 图像查询索引
CREATE INDEX idx_virtual_ip_images_virtual_ip_id ON virtual_ip_images(virtual_ip_id);
CREATE INDEX idx_virtual_ip_images_category ON virtual_ip_images(category);
```

### 2. 连接池调优

根据应用负载调整连接池配置：

```python
# 高负载环境
"pool_size": 50,
"max_overflow": 10,
"pool_recycle": 7200
```

### 3. 查询优化

- 使用合适的数据类型
- 避免SELECT *查询
- 合理使用分页
- 启用查询缓存

## 备份与恢复

### 数据备份

```bash
# 创建数据备份
mysqldump -h127.0.0.1 -P13306 -uroot -pPa88word ai_video_studio > backup.sql
```

### 数据恢复

```bash
# 从备份恢复
mysql -h127.0.0.1 -P13306 -uroot -pPa88word ai_video_studio < backup.sql
```

## 安全建议

1. **生产环境**：
   - 使用强密码
   - 创建专用数据库用户
   - 限制网络访问权限
   - 启用SSL连接

2. **开发环境**：
   - 不要在代码中硬编码密码
   - 使用环境变量管理敏感信息
   - 定期更新依赖包

## 监控与日志

### 启用SQL日志

在开发环境中启用SQL查询日志：

```python
# 在database.py中添加
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # 启用SQL日志
    **engine_config
)
```

### 性能监控

使用MySQL的性能监控工具：

```sql
-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log';

-- 查看连接状态
SHOW STATUS LIKE 'Connections';

-- 查看当前进程
SHOW PROCESSLIST;
```