# AI短剧制作工作流平台 - 前端

这是一个以虚拟IP为中心的AI短剧制作工作流平台的前端应用，基于 Next.js 16（App Router）构建。

> 快速跑通全栈开发环境建议从根目录 `README.md` / `README_EN.md` 与 `docker/README.md` 开始。

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

- Node.js 22.20.0（与生产镜像一致）
- npm 或 yarn

### 安装依赖

```bash
npm install
# 或
yarn install
```

### 环境配置

1. 配置环境变量（推荐使用 `.env.local`）：

```bash
# API服务地址
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 启动开发服务器

```bash
npm run dev
# 或
yarn dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看应用。

## 主要功能

### 虚拟IP管理

- **虚拟IP列表**: 查看所有虚拟IP，支持搜索和筛选
- **虚拟IP详情**: 查看虚拟IP详细信息，包括背景故事、风格提示等
- **创建/编辑虚拟IP**: 创建新的虚拟IP或编辑现有IP信息
- **删除虚拟IP**: 删除不需要的虚拟IP

### AI图像生成

- **多种生成风格**: 支持写实、动漫、卡通三种风格
- **多种图像类别**: 支持肖像、全身像、场景、动作、表情等类别
- **智能提示词优化**: 自动优化生成提示词，提高图像质量
- **多AI服务支持**: 支持OpenAI DALL-E、Stability AI等多种服务
- **生成历史管理**: 查看和管理AI生成的图像

### 图像资源管理

- **图像上传**: 支持手动上传图像文件
- **AI生成**: 使用AI服务生成虚拟IP图像
- **分类管理**: 按类别组织和管理图像
- **标签系统**: 为图像添加标签，便于搜索和管理
- **默认图像设置**: 为虚拟IP设置默认显示图像
- **批量操作**: 支持批量删除、设置默认等操作

## 页面结构

```
src/app/
├── page.tsx                 # 主页
├── environments/            # 环境资产
├── stories/                 # 故事创作
├── episodes/                # 分集/分镜相关页面
├── virtual-ip/             # 虚拟IP管理
│   ├── page.tsx            # 虚拟IP列表
│   └── [id]/               # 虚拟IP详情
│       ├── page.tsx        # 虚拟IP详情页
│       └── images/         # 图像管理
│           └── page.tsx    # 图像管理页面
├── login/                  # 登录页面
├── register/               # 注册页面
├── tasks/                  # 任务管理
└── scripts/                # 剧本相关页面
```

## AI图像生成使用指南

### 1. 配置AI服务

确保后端已正确配置AI服务API Key：

- **OpenAI DALL-E** (推荐): 配置 `OPENAI_API_KEY`
- **Stability AI**: 配置 `STABILITY_API_KEY`
- **自定义AI服务**: 配置 `AI_SERVICE_URL` 和 `AI_API_KEY`

### 2. 生成图像

1. 进入虚拟IP详情页面
2. 点击"管理图像"按钮
3. 选择"AI生成图像"模式
4. 配置生成参数：
   - **生成风格**: 选择写实、动漫或卡通风格
   - **图像类别**: 选择肖像、全身像、场景等
   - **额外提示词**: 添加具体的描述词（可选）
   - **设为默认**: 是否设为默认图像
5. 点击"开始生成"

### 3. 生成参数说明

#### 生成风格

- **写实风格**: 真实照片风格，适合正式场合
- **动漫风格**: 日式动漫风格，适合二次元内容
- **卡通风格**: 欧美卡通风格，适合儿童内容

#### 图像类别

- **肖像**: 头像、半身像，突出面部特征
- **全身像**: 完整人物形象，展示整体造型
- **场景**: 背景场景，展示环境氛围
- **动作**: 动态姿势，展示动作状态
- **表情**: 面部表情特写，展示情感状态

#### 额外提示词示例

- 表情相关: "smiling", "serious", "happy", "confident"
- 环境相关: "outdoor", "indoor", "studio", "natural lighting"
- 风格相关: "professional", "casual", "elegant", "cute"
- 道具相关: "holding book", "wearing hat", "with flowers"

### 4. 管理生成的图像

- **查看生成历史**: 所有AI生成的图像都会保存并显示
- **设置默认图像**: 点击"设默认"按钮设置默认显示图像
- **删除图像**: 点击"删除"按钮移除不需要的图像
- **分类筛选**: 使用分类按钮筛选不同类型的图像

## 技术栈

- **框架**: Next.js 16 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **状态管理**: React Hooks
- **HTTP客户端**: Fetch API
- **UI组件**: 自定义组件 + Tailwind CSS

## 开发指南

### 添加新页面

1. 在 `src/app/` 下创建新的目录和页面文件
2. 在 `src/utils/api/endpoints/*` 与 `src/utils/api/types/*` 中添加相应的 API 请求方法和类型定义（HTTP 客户端放在 `src/utils/api/client.ts`）
3. 更新导航菜单（如果需要）

### 添加新功能

1. 创建功能组件
2. 添加相应的API接口
3. 更新类型定义
4. 添加错误处理和加载状态

### 样式指南

- 使用 Tailwind CSS 类名
- 遵循响应式设计原则
- 保持一致的视觉风格
- 使用语义化的颜色命名

## 部署

### Vercel部署（推荐）

```bash
# 安装Vercel CLI
npm i -g vercel

# 部署
vercel
```

### 其他平台

```bash
# 构建生产版本
npm run build

# 启动生产服务器
npm start
```

## 环境变量

```bash
# API服务地址
NEXT_PUBLIC_API_URL=http://localhost:8000

# 其他配置
NEXT_PUBLIC_APP_NAME=AI短剧制作平台

# 是否默认启用规范化叙事结构读取（分镜页实验开关）
NEXT_PUBLIC_USE_NORMALIZED_BY_DEFAULT=false
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
