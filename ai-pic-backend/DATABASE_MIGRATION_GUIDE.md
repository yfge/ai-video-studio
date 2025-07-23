# 数据库迁移指南

本项目使用 Alembic 进行数据库迁移管理。

## 快速开始

### 使用 Python 脚本（推荐）

```bash
# 生成新的迁移文件
python migrate.py generate

# 应用迁移到数据库
python migrate.py upgrade

# 查看当前迁移版本
python migrate.py current

# 查看迁移历史
python migrate.py history

# 回退到上一个版本
python migrate.py downgrade

# 重置数据库（危险操作）
python migrate.py reset
```

### 使用 Windows 批处理文件

```cmd
# 生成新的迁移文件
migrate.bat generate

# 应用迁移到数据库
migrate.bat upgrade

# 查看当前迁移版本
migrate.bat current

# 查看迁移历史
migrate.bat history

# 回退到上一个版本
migrate.bat downgrade

# 重置数据库（危险操作）
migrate.bat reset
```

### 直接使用 Alembic 命令

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 生成迁移文件
alembic revision --autogenerate -m "描述信息"

# 应用迁移
alembic upgrade head

# 查看当前版本
alembic current

# 查看历史
alembic history

# 回退一个版本
alembic downgrade -1

# 回退到特定版本
alembic downgrade <revision_id>
```

## 工作流程

### 1. 修改模型后生成迁移

当你修改了 `app/models/` 目录下的模型文件后：

```bash
python migrate.py generate
```

系统会提示你输入迁移描述信息，然后自动生成迁移文件。

### 2. 检查生成的迁移文件

生成的迁移文件位于 `alembic/versions/` 目录下。请检查文件内容确保迁移操作正确。

### 3. 应用迁移

```bash
python migrate.py upgrade
```

### 4. 验证迁移

```bash
python migrate.py current
```

## 注意事项

### 1. 数据库备份

在应用迁移前，特别是在生产环境中，请务必备份数据库。

### 2. 迁移文件管理

- 不要手动删除已经应用的迁移文件
- 不要修改已经应用的迁移文件
- 迁移文件应该提交到版本控制系统

### 3. 模型字段命名

避免使用 SQLAlchemy 保留字段名，如：
- `metadata` - 使用 `extra_metadata` 代替
- `query` - 使用其他名称

### 4. 环境变量

确保 `.env` 文件中的 `DATABASE_URL` 配置正确。

## 常见问题

### Q: 迁移失败怎么办？

A: 
1. 检查模型定义是否正确
2. 检查数据库连接是否正常
3. 查看错误日志，修复问题后重新生成迁移

### Q: 如何回退迁移？

A: 
```bash
python migrate.py downgrade
```

### Q: 如何重置数据库？

A: 
```bash
python migrate.py reset
```
**警告：这将删除所有数据！**

### Q: 迁移文件冲突怎么办？

A: 
1. 使用 `alembic merge` 合并冲突的迁移
2. 或者删除冲突的迁移文件，重新生成

## 文件结构

```
ai-pic-backend/
├── alembic/                 # Alembic 配置目录
│   ├── versions/           # 迁移文件目录
│   ├── env.py             # 环境配置
│   └── script.py.mako     # 迁移模板
├── alembic.ini            # Alembic 配置文件
├── migrate.py             # 迁移管理脚本
├── migrate.bat            # Windows 批处理文件
└── app/
    └── models/            # 数据模型目录
        ├── user.py
        ├── virtual_ip.py
        └── script.py
```

## 开发建议

1. 每次模型变更后立即生成迁移
2. 为每个迁移添加有意义的描述信息
3. 在团队开发中，及时同步迁移文件
4. 定期检查数据库结构与模型定义的一致性 