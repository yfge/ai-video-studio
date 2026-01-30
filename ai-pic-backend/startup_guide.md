# 后端启动指南

## 🚀 快速启动

### 1. 确保在正确的目录

```bash
cd ai-pic-backend
```

### 2. 创建虚拟环境（推荐）

```bash
# 使用venv
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量示例文件
cp env.example .env

# 编辑.env文件，配置必要的环境变量
# 至少需要修改SECRET_KEY
```

### 5. 启动开发服务器

```bash
# 方式1：直接运行
python main.py

# 方式2：使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问应用

- API服务: http://localhost:8000
- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

## 🔧 故障排除

### 问题1: 依赖安装失败

**错误信息**: `pip install -r requirements.txt` 失败

**解决方案**:

```bash
# 升级pip
pip install --upgrade pip

# 安装编译工具（Windows）
# 下载并安装Visual Studio Build Tools

# 使用conda（如果pip有问题）
conda install -c conda-forge fastapi uvicorn
```

### 问题2: 端口被占用

**错误信息**: `Port 8000 is already in use`

**解决方案**:

```bash
# 查找占用端口的进程
netstat -ano | findstr :8000

# 终止进程（替换PID为实际的进程ID）
taskkill /PID <PID> /F

# 或使用其他端口
uvicorn main:app --reload --port 8001
```

### 问题3: 数据库错误

**错误信息**: `sqlite3.OperationalError`

**解决方案**:

```bash
# 删除现有数据库文件（如果存在）
rm ai_pic.db

# 重新启动应用，会自动创建数据库
python main.py
```

### 问题4: 导入错误

**错误信息**: `ModuleNotFoundError`

**解决方案**:

```bash
# 确保在正确的目录
pwd  # 应该显示 .../ai-pic-backend

# 重新安装依赖
pip install -r requirements.txt

# 检查Python路径
python -c "import sys; print(sys.path)"
```

## 📱 测试API

启动成功后，你可以测试以下API端点：

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

### 2. 用户注册

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### 3. 用户登录

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

## 🛠️ 开发命令

```bash
# 开发模式（推荐）
python main.py

# 开发模式（使用uvicorn）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 代码检查
pip install flake8
flake8 app/

# 运行测试
pip install pytest
pytest
```

## 📝 注意事项

1. **虚拟环境**: 建议使用虚拟环境避免依赖冲突
2. **环境变量**: 必须配置.env文件中的SECRET_KEY
3. **数据库**: 首次运行会自动创建SQLite数据库
4. **端口冲突**: 如果8000端口被占用，会自动使用下一个可用端口
5. **文件权限**: 确保uploads目录有写入权限

## 🆘 获取帮助

如果遇到其他问题，请检查：

1. Python版本是否为3.8+
2. 是否在正确的目录下
3. 依赖是否正确安装
4. 环境变量是否正确配置
5. 端口是否被其他程序占用

## 🔗 相关链接

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Pydantic文档](https://pydantic-docs.helpmanual.io/)
