# AI短剧制作工作流平台 - 后端

这是一个以虚拟IP为中心的AI短剧制作工作流平台的后端服务，所有大模型能力均通过外部API调用。

## 核心功能

- **虚拟IP管理**: 虚拟IP档案管理、图像资源管理
- **AI图像生成**: 支持多种AI服务生成虚拟IP图像
- **剧本与内容生产**: 剧本创作、内容生成
- **AI能力集成**: 集成多种AI服务API
- **任务与工作流编排**: 任务管理、工作流自动化
- **素材与资源管理**: 图像、音频、视频资源管理
- **协作与权限**: 团队协作、权限控制
- **审核与质量控制**: 内容审核、质量检查
- **成本与调用统计**: API调用统计、成本分析
- **用户与商业化**: 用户管理、商业化功能
- **平台基础设施**: 系统架构、性能优化
- **安全与合规**: 数据安全、合规性

## 快速开始

### 环境要求

- Python 3.8+
- SQLite (默认) 或 PostgreSQL
- Redis (可选)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 环境配置

1. 复制环境变量文件：
```bash
cp env.example .env
```

2. 配置环境变量：
```bash
# 基础配置
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./ai_pic.db

# AI服务配置 (至少配置一个)
OPENAI_API_KEY=your-openai-api-key-here
STABILITY_API_KEY=your-stability-api-key-here
AI_SERVICE_URL=your-custom-ai-service-url
AI_API_KEY=your-custom-ai-service-key
```

### AI服务配置

平台支持多种AI图像生成服务：

#### 1. OpenAI DALL-E (推荐)
- 注册 [OpenAI](https://platform.openai.com/)
- 获取API Key
- 配置环境变量：`OPENAI_API_KEY=your-key`

#### 2. Stability AI
- 注册 [Stability AI](https://platform.stability.ai/)
- 获取API Key
- 配置环境变量：`STABILITY_API_KEY=your-key`

#### 3. 自定义AI服务
- 配置服务URL和API Key
- 环境变量：`AI_SERVICE_URL` 和 `AI_API_KEY`

### 启动服务

```bash
# 开发模式
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心API

### 虚拟IP管理

- `GET /api/v1/virtual-ips` - 获取虚拟IP列表
- `POST /api/v1/virtual-ips` - 创建虚拟IP
- `GET /api/v1/virtual-ips/{id}` - 获取虚拟IP详情
- `PUT /api/v1/virtual-ips/{id}` - 更新虚拟IP
- `DELETE /api/v1/virtual-ips/{id}` - 删除虚拟IP

### 虚拟IP图像管理

- `GET /api/v1/virtual-ips/{id}/images` - 获取虚拟IP图像列表
- `POST /api/v1/virtual-ips/{id}/images` - 上传图像
- `POST /api/v1/virtual-ips/{id}/images/generate` - **AI生成图像**
- `PUT /api/v1/virtual-ips/{id}/images/{image_id}` - 更新图像信息
- `DELETE /api/v1/virtual-ips/{id}/images/{image_id}` - 删除图像
- `POST /api/v1/virtual-ips/{id}/images/{image_id}/set-default` - 设置默认图像

## AI图像生成功能

### 支持的生成风格

- **写实风格** (realistic): 真实照片风格
- **动漫风格** (anime): 日式动漫风格
- **卡通风格** (cartoon): 欧美卡通风格

### 支持的图像类别

- **肖像** (portrait): 头像、半身像
- **全身像** (full_body): 完整人物形象
- **场景** (scene): 背景场景
- **动作** (action): 动态姿势
- **表情** (emotion): 面部表情特写

### 生成参数

- `style`: 生成风格
- `category`: 图像类别
- `additional_prompts`: 额外提示词（可选）
- `is_default`: 是否设为默认图像

### 示例请求

```bash
curl -X POST "http://localhost:8000/api/v1/virtual-ips/1/images/generate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "style=realistic&category=portrait&additional_prompts=smiling,outdoor&is_default=true"
```

## 数据库结构

### 虚拟IP表 (virtual_ips)
- id: 主键
- name: IP名称
- description: 描述
- tags: 标签
- background_story: 背景故事
- style_prompt: 风格提示词
- is_active: 是否激活
- is_public: 是否公开
- created_at: 创建时间
- updated_at: 更新时间

### 虚拟IP图像表 (virtual_ip_images)
- id: 主键
- virtual_ip_id: 虚拟IP ID
- file_path: 文件路径
- category: 图像类别
- tags: 标签
- is_default: 是否默认图像
- metadata: 元数据（JSON）
- created_at: 创建时间
- updated_at: 更新时间

## 开发指南

### 添加新的AI服务

1. 在 `app/services/ai_service.py` 中添加新的生成方法
2. 在配置文件中添加相应的API Key配置
3. 在 `generate_virtual_ip_image` 方法中添加新服务到服务列表

### 扩展图像类别

1. 更新前端图像类别选项
2. 在后端验证中添加新类别
3. 更新文档和示例

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t ai-pic-backend .

# 运行容器
docker run -p 8000:8000 --env-file .env ai-pic-backend
```

### 生产环境配置

1. 使用PostgreSQL数据库
2. 配置Redis缓存
3. 设置反向代理（Nginx）
4. 配置SSL证书
5. 设置监控和日志

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License 