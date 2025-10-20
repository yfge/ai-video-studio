# AI图像生成诊断系统使用指南

## 概览

我们为AI图像生成系统创建了完整的诊断机制，包括多种测试工具和方法来诊断和修复问题。

## 🚀 快速开始

### 1. 简化诊断（推荐）

最简单的方法是使用独立的诊断脚本：

```bash
python simple_diagnostic.py
```

这个脚本不需要启动完整的FastAPI应用，可以快速检测：
- ✅ 环境配置
- ✅ 文件系统权限
- ✅ OpenAI API连接
- ✅ 图像生成功能

### 2. 通过API诊断

如果FastAPI服务正在运行，可以通过API进行诊断：

```bash
# 快速健康检查（无需认证）
curl http://localhost:8000/api/v1/diagnostic/health

# 完整诊断（需要登录后获取token）
curl -X POST http://localhost:8000/api/v1/diagnostic/full \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. pytest测试框架

使用专业的pytest框架进行全面测试：

```bash
# 检查测试环境
python run_pytest.py --check

# 运行诊断测试
python run_pytest.py --diagnostic

# 运行快速测试
python run_pytest.py --quick

# 运行完整测试套件
python run_pytest.py --all
```

## 📋 测试项目详解

### 环境配置检查
检查以下环境变量是否正确配置：

**必需配置:**
- `OPENAI_API_KEY` - OpenAI API密钥

**可选配置:**
- `UPLOAD_DIR` - 文件上传目录（默认: `./uploads`）
- `ALIYUN_ACCESS_KEY_ID` - 阿里云访问密钥ID
- `ALIYUN_ACCESS_KEY_SECRET` - 阿里云访问密钥
- `ALIYUN_OSS_ENDPOINT` - OSS端点
- `ALIYUN_OSS_BUCKET` - OSS存储桶名称

### OpenAI API测试
验证OpenAI API连接和权限：
- 测试API密钥有效性
- 验证账户余额
- 检查网络连接

### 文件系统测试
验证本地文件操作：
- 创建上传目录
- 测试文件读写权限
- 检查磁盘空间

### 图像生成测试
端到端测试图像生成流程：
- 调用OpenAI DALL-E API
- 处理base64图像数据
- 保存到本地文件系统
- UUID命名规范
- 可选OSS上传

### 数据库测试
验证数据库连接和操作：
- 数据库连接状态
- 表结构检查
- 基本CRUD操作

## 🛠️ 故障排除

### 常见问题及解决方案

#### 1. OpenAI API失败

**错误症状:**
```
❌ OpenAI API: API返回错误: 401 - Unauthorized
```

**解决方案:**
```bash
# 检查API密钥
echo $OPENAI_API_KEY

# 设置API密钥
export OPENAI_API_KEY="your-openai-api-key-here"

# 验证API密钥格式（应该以sk-开头）
```

#### 2. 文件系统权限问题

**错误症状:**
```
❌ 文件系统: Permission denied
```

**解决方案:**
```bash
# 创建上传目录
mkdir -p uploads

# 设置权限
chmod 755 uploads

# 检查权限
ls -la uploads/
```

#### 3. 图像生成403错误

**错误症状:**
```
❌ 图像生成: Client error '403 Server failed to authenticate
```

**解决方案:**
- 检查OpenAI账户余额
- 验证API密钥权限
- 确认API请求限制

#### 4. OSS上传失败

**错误症状:**
```
❌ OSS上传失败: 'OSSService' object has no attribute 'upload_file'
```

**解决方案:**
- 检查OSS配置是否完整
- 验证阿里云账户权限
- 确认存储桶访问策略

#### 5. 登录时报错：AttributeError: module 'bcrypt' has no attribute '__about__'

**错误症状:**
```
error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**原因:**
- `passlib 1.7.x` 与 `bcrypt 4.x` 的元数据接口不兼容，导致读取版本时异常。

**解决方案:**
1. 将 `bcrypt` 锁定为 `<4`（例如 `3.2.2`）。本项目的 `requirements.txt` 已固定：
   ```
   passlib[bcrypt]==1.7.4
   bcrypt==3.2.2
   ```
2. 重新安装依赖：
   ```bash
   pip install -r ai-pic-backend/requirements.txt
   ```

## 📊 测试报告

### 报告类型

1. **控制台输出** - 实时显示测试进度和结果
2. **JSON报告** - 详细的机器可读格式
3. **HTML报告** - pytest生成的可视化报告（使用`--coverage`选项）

### 报告文件

- `simple_diagnostic_report.json` - 简化诊断报告
- `diagnostic_report.json` - 完整诊断报告  
- `htmlcov/index.html` - pytest覆盖率报告

### 报告解读

```json
{
  "summary": {
    "total_tests": 4,
    "passed_tests": 3,
    "failed_tests": 1,
    "success_rate": "75.0%"
  },
  "results": {
    "测试项目": {
      "success": true,
      "details": "详细信息",
      "error": "",
      "timestamp": "2023-08-20T17:45:00"
    }
  },
  "errors": [
    "具体错误信息"
  ]
}
```

## 🔄 持续监控

### 定期健康检查

建议定期运行诊断检查：

```bash
# 每日快速检查
python simple_diagnostic.py

# 每周完整测试
python run_pytest.py --all

# 部署前验证
python run_pytest.py --external
```

### 集成到CI/CD

可以将测试集成到CI/CD流水线：

```yaml
# .github/workflows/test.yml
name: AI Image Generation Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run diagnostic tests
      run: python run_pytest.py --diagnostic
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## 📚 API文档

### 诊断API端点

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/diagnostic/health` | GET | 否 | 快速健康检查 |
| `/api/v1/diagnostic/full` | POST | 是 | 完整诊断 |
| `/api/v1/diagnostic/openai` | POST | 是 | OpenAI API测试 |
| `/api/v1/diagnostic/oss` | POST | 是 | OSS服务测试 |
| `/api/v1/diagnostic/database` | POST | 是 | 数据库测试 |
| `/api/v1/diagnostic/filesystem` | POST | 是 | 文件系统测试 |
| `/api/v1/diagnostic/end-to-end` | POST | 是 | 端到端测试 |

### 使用示例

```bash
# 健康检查
curl http://localhost:8000/api/v1/diagnostic/health

# 获取认证token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=Ai7dio" | jq -r '.access_token')

# 运行完整诊断
curl -X POST http://localhost:8000/api/v1/diagnostic/full \
  -H "Authorization: Bearer $TOKEN"
```

## 🎯 最佳实践

### 开发环境

1. **开发前检查** - 启动开发前运行快速诊断
2. **功能测试** - 每个新功能都要有对应的诊断测试
3. **错误调试** - 遇到问题时先运行诊断获取详细信息

### 生产环境

1. **部署验证** - 部署后立即运行完整诊断
2. **监控告警** - 设置定期健康检查和告警
3. **问题排查** - 用户反馈问题时先运行诊断

### 维护建议

1. **定期更新** - 保持诊断脚本与主应用同步
2. **扩展测试** - 添加新功能时同步添加诊断测试
3. **文档更新** - 及时更新故障排除指南

## 🆘 获取帮助

如果诊断系统本身出现问题：

1. **检查依赖** - 确保所需Python包已安装
2. **查看日志** - 检查控制台输出和错误信息
3. **简化测试** - 使用`simple_diagnostic.py`进行基础检查
4. **重新安装** - 重新安装pytest和相关依赖

---

💡 **提示:** 定期运行诊断可以预防问题发生，建议将诊断检查纳入日常开发流程。
