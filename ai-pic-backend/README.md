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
- MySQL 8.0+ (推荐) 或 SQLite (开发环境)
- Redis (可选)

### 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 或使用conda环境
conda create -n py311 python=3.11
conda activate py311
pip install -r requirements.txt
```

### 数据库配置

#### MySQL配置 (推荐)

1. 启动MySQL数据库：
```bash
# 使用Docker启动MySQL
docker run --name mysql-ai-studio \
  -e MYSQL_ROOT_PASSWORD=Pa88word \
  -e MYSQL_DATABASE=ai_video_studio \
  -p 13306:3306 \
  -d mysql:8.0
```

2. 配置环境变量：
```bash
# .env 文件
DATABASE_URL=mysql+pymysql://root:Pa88word@127.0.0.1:13306/ai_video_studio?charset=utf8mb4
```

#### 初始化数据库

```bash
# 使用管理脚本初始化数据库
python manage.py migration init
python manage.py migration upgrade

# 运行初始数据种子
python manage.py seed run --all

# 验证数据库状态
python manage.py migration status
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
DATABASE_URL=mysql+pymysql://root:Pa88word@127.0.0.1:13306/ai_video_studio?charset=utf8mb4

# 开发环境可使用SQLite
# DATABASE_URL=sqlite:///./ai_pic.db

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
# 使用管理脚本启动（推荐）
python manage.py server run --host 0.0.0.0 --port 8000 --reload

# 生产模式
python manage.py server production --workers 4

# 直接启动
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 快速启动（自动检查和升级数据库）
python manage.py quickstart
```

## 数据库管理

本项目实现了强大的数据库迁移和管理系统，提供Django风格的管理命令：

### 迁移管理

```bash
# 查看所有可用命令
python manage.py

# 创建新迁移
python manage.py migration create -m "添加新字段"

# 升级数据库
python manage.py migration upgrade

# 查看迁移状态
python manage.py migration status

# 查看迁移历史
python manage.py migration history

# 验证迁移文件
python manage.py migration validate
```

### 数据种子管理

```bash
# 创建新数据种子
python manage.py seed create -n "initial_data"

# 运行特定种子
python manage.py seed run -n "initial_data"

# 运行所有种子
python manage.py seed run --all
```

### 开发工具

```bash
# 项目配置检查
python manage.py dev check

# 运行测试
python manage.py dev test

# 代码质量检查
python manage.py dev lint

# 代码格式化
python manage.py dev format

# 启动交互式Shell
python manage.py dev shell
```

### 数据库迁移API

系统还提供REST API接口管理迁移：

- `GET /api/v1/migrations/status` - 获取迁移状态
- `GET /api/v1/migrations/history` - 获取迁移历史
- `POST /api/v1/migrations/upgrade` - 升级数据库
- `GET /api/v1/migrations/health` - 系统健康检查

详细迁移系统文档请参考：[MIGRATION_SYSTEM_GUIDE.md](./MIGRATION_SYSTEM_GUIDE.md)

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

本项目使用完整的关系型数据库设计，支持从虚拟IP到完整短剧制作的全流程：

### 核心实体表

#### 虚拟IP表 (virtual_ips)
- id: 主键
- name: IP名称
- description: 描述
- tags: 标签（JSON）
- background_story: 背景故事
- style_prompt: 风格提示词
- style_reference_images: 参考图像（JSON）
- default_avatar_url: 默认头像URL
- is_active: 是否激活
- is_public: 是否公开
- created_at: 创建时间
- updated_at: 更新时间

#### 虚拟IP图像表 (virtual_ip_images)
- id: 主键
- virtual_ip_id: 虚拟IP ID
- filename: 文件名
- original_filename: 原始文件名
- file_path: 文件路径
- file_size: 文件大小
- mime_type: MIME类型
- category: 图像类别
- subcategory: 子类别
- tags: 标签（JSON）
- prompt: 生成提示词
- ai_model: AI模型名称
- generation_params: 生成参数（JSON）
- is_default: 是否默认图像
- is_public: 是否公开
- created_at: 创建时间

#### 故事表 (stories)
- id: 主键
- title: 故事标题
- genre: 故事类型
- theme: 故事主题
- target_audience: 目标受众
- duration_minutes: 预计总时长
- premise: 故事前提
- synopsis: 故事概要
- main_conflict: 主要冲突
- resolution: 解决方案
- main_characters: 主要角色（JSON）
- character_relationships: 角色关系（JSON）
- setting_time: 时间设定
- setting_location: 地点设定
- world_building: 世界观设定
- generation_prompt: 生成提示词
- ai_model: 使用的AI模型
- generation_params: 生成参数（JSON）
- status: 状态（draft, approved, published）
- is_public: 是否公开
- tags: 标签（JSON）
- extra_metadata: 额外元数据（JSON）
- created_at: 创建时间
- updated_at: 更新时间

#### 剧集表 (episodes)
- id: 主键
- story_id: 故事ID（外键）
- episode_number: 集数
- title: 剧集标题
- summary: 剧集概要
- plot_points: 情节要点（JSON）
- character_arcs: 角色发展（JSON）
- conflicts: 冲突点（JSON）
- duration_minutes: 预计时长
- scene_count: 场景数量
- generation_prompt: 生成提示词
- ai_model: 使用的AI模型
- generation_params: 生成参数（JSON）
- status: 状态
- tags: 标签（JSON）
- extra_metadata: 额外元数据（JSON）
- created_at: 创建时间
- updated_at: 更新时间

#### 剧本表 (scripts)
- id: 主键
- episode_id: 剧集ID（外键）
- title: 剧本标题
- content: 剧本内容
- scenes: 场景列表（JSON）
- dialogues: 对话列表（JSON）
- stage_directions: 舞台指示（JSON）
- format_type: 剧本格式类型
- language: 语言
- page_count: 页数
- word_count: 字数
- character_count: 字符数
- generation_prompt: 生成提示词
- ai_model: 使用的AI模型
- generation_params: 生成参数（JSON）
- status: 状态
- version: 版本号
- tags: 标签（JSON）
- extra_metadata: 额外元数据（JSON）
- created_at: 创建时间
- updated_at: 更新时间

### 关系表

#### 故事角色表 (story_characters)
- id: 主键
- story_id: 故事ID（外键）
- virtual_ip_id: 虚拟IP ID（外键）
- character_name: 角色名称
- role_type: 角色类型（protagonist, antagonist, supporting）
- importance: 重要度（1-5）
- personality: 性格特点
- background: 背景故事
- motivation: 动机
- character_arc: 角色发展弧线
- relationships: 与其他角色的关系（JSON）
- created_at: 创建时间
- updated_at: 更新时间

### 系统支持表

#### 用户表 (users)
- id: 主键
- username: 用户名（唯一）
- email: 邮箱（唯一）
- hashed_password: 加密密码
- full_name: 全名
- is_active: 是否激活
- is_superuser: 是否超级用户
- created_at: 创建时间
- updated_at: 更新时间

#### 任务表 (tasks)
- id: 主键
- title: 任务标题
- description: 任务描述
- task_type: 任务类型（IMAGE_GENERATION, IMAGE_EDIT, IMAGE_ENHANCEMENT）
- status: 状态（PENDING, PROCESSING, COMPLETED, FAILED）
- prompt: 提示词
- parameters: 参数
- result_file_path: 结果文件路径
- error_message: 错误信息
- user_id: 用户ID（外键）
- created_at: 创建时间
- updated_at: 更新时间

#### 图像表 (images)
- id: 主键
- filename: 文件名
- original_filename: 原始文件名
- file_path: 文件路径
- file_size: 文件大小
- mime_type: MIME类型
- description: 描述
- prompt: 提示词
- user_id: 用户ID（外键）
- created_at: 创建时间

#### 脚本模板表 (script_templates)
- id: 主键
- name: 模板名称
- category: 模板分类
- template_content: 模板内容
- structure: 结构定义（JSON）
- variables: 变量定义（JSON）
- usage_count: 使用次数
- rating: 评分
- is_active: 是否激活
- is_public: 是否公开
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

# 使用Docker Compose启动完整服务
docker-compose up -d

# 或单独运行容器
docker run -p 8000:8000 --env-file .env ai-pic-backend
```

### 生产环境配置

1. **数据库配置**
   - 使用MySQL 8.0+作为主数据库
   - 配置数据库连接池和优化参数
   - 设置定期备份策略

2. **迁移管理**
   - 配置迁移中间件保护
   - 设置自动备份和回滚点
   - 监控迁移状态和健康检查

3. **基础设施**
   - 配置Redis缓存
   - 设置反向代理（Nginx）
   - 配置SSL证书
   - 设置监控和日志

4. **部署流程**
   ```bash
   # 1. 拉取代码
   git pull origin main
   
   # 2. 检查迁移状态
   python manage.py migration status
   
   # 3. 执行迁移（带备份）
   python manage.py migration upgrade --backup
   
   # 4. 验证部署
   python manage.py dev check
   
   # 5. 启动服务
   python manage.py server production
   ```

### 监控和维护

```bash
# 健康检查
curl http://localhost:8000/api/v1/migrations/health

# 迁移状态监控
curl http://localhost:8000/api/v1/migrations/status

# 定期清理回滚点
python manage.py migration cleanup-rollbacks --days 30
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License 