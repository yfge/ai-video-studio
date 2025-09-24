# AI提示词管理系统

本系统提供了统一的AI提示词管理功能，支持各种AI任务的提示词模板化、版本控制和动态渲染。

## 功能特性

### 🎯 核心功能
- **模板管理**: 支持Jinja2模板语法的提示词模板
- **分类组织**: 按功能类别组织提示词（角色、故事、剧集、剧本、图像等）
- **变量验证**: 自动验证模板变量的类型和值
- **动态渲染**: 基于变量动态生成最终提示词
- **版本控制**: 支持模板版本管理和元数据
- **API接口**: 完整的RESTful API支持

### 📁 目录结构
```
app/prompts/
├── __init__.py          # 模块初始化
├── manager.py           # 提示词管理器核心逻辑
├── templates.py         # 模板枚举和常量定义
├── templates/           # 提示词模板文件夹
│   ├── virtual_ip_creation.txt    # 虚拟IP创建模板
│   ├── virtual_ip_creation.yaml   # 虚拟IP创建元数据
│   ├── story_outline.txt          # 故事大纲模板
│   ├── story_outline.yaml         # 故事大纲元数据
│   ├── episode_generation.txt     # 剧集生成模板
│   ├── episode_generation.yaml    # 剧集生成元数据
│   ├── script_generation.txt      # 剧本生成模板
│   ├── script_generation.yaml     # 剧本生成元数据
│   ├── image_generation.txt       # 图像生成模板
│   └── image_generation.yaml      # 图像生成元数据
└── README.md            # 说明文档
```

## 模板分类

### 🎭 角色相关 (character)
- **virtual_ip_creation**: 虚拟IP角色创建
- 生成角色的详细设定、背景故事、性格特征等

### 📖 故事相关 (story)  
- **story_outline**: 故事大纲生成
- 基于角色和设定生成完整的故事概要

### 📺 剧集相关 (episode)
- **episode_generation**: 剧集大纲生成
- 将故事分解为具体的剧集内容

### 📝 剧本相关 (script)
- **script_generation**: 剧本生成
- 基于剧集信息生成详细的可拍摄剧本

### 🖼️ 图像相关 (image)
- **image_generation**: AI图像生成提示词
- 为角色生成专业的AI绘画提示词

## API使用指南

### 认证
所有API请求都需要Bearer Token认证：
```bash
Authorization: Bearer <your_token>
```

### 获取模板列表
```bash
GET /api/v1/prompts/templates
GET /api/v1/prompts/templates?category=character
```

### 获取模板信息
```bash
GET /api/v1/prompts/templates/{template_name}
```

### 渲染提示词
```bash
POST /api/v1/prompts/render
Content-Type: application/json

{
    "template_name": "virtual_ip_creation",
    "variables": {
        "name": "小雅",
        "description": "活泼可爱的女孩",
        "age": "22岁",
        "gender": "女性"
    }
}
```

### 快捷生成API
系统提供了针对特定工作流的快捷API：

#### 生成角色提示词
```bash
POST /api/v1/prompts/generate/character
{
    "name": "小雅",
    "description": "活泼可爱的女孩",
    "age": "22岁",
    "gender": "女性"
}
```

#### 生成故事提示词
```bash
POST /api/v1/prompts/generate/story
{
    "title": "友情的力量",
    "genre": "剧情",
    "characters": [
        {"name": "小雅", "description": "活泼女孩"}
    ]
}
```

#### 生成图像提示词
```bash
POST /api/v1/prompts/generate/image
{
    "character_name": "小雅",
    "style": "realistic",
    "category": "portrait"
}
```

## 编程使用示例

### Python代码示例
```python
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate

# 渲染角色创建提示词
variables = {
    "name": "小雅",
    "description": "活泼可爱的年轻女孩",
    "age": "22岁",
    "gender": "女性",
    "personality_traits": ["活泼", "好奇", "乐观"]
}

prompt = prompt_manager.render_prompt(
    PromptTemplate.VIRTUAL_IP_CREATION.value,
    variables
)

print(prompt)
```

### 在AI服务中使用
```python
# 在ai_service.py中
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate

async def generate_character(self, **kwargs):
    # 使用模板渲染提示词
    prompt = prompt_manager.render_prompt(
        PromptTemplate.VIRTUAL_IP_CREATION.value,
        kwargs
    )
    
    # 调用AI生成
    result = await self._call_text_generation_service(prompt, "character")
    return result
```

## 创建新模板

### 1. 创建模板文件
在 `templates/` 目录下创建 `.txt` 文件：
```txt
# my_template.txt
你是一个专业的{{role}}，请根据以下信息生成{{task}}：

## 输入信息
{% for item in items %}
- {{item.name}}: {{item.description}}
{% endfor %}

## 生成要求
请生成{{output_format}}格式的内容。
```

### 2. 创建元数据文件
创建对应的 `.yaml` 文件：
```yaml
# my_template.yaml
name: my_template
description: "我的自定义模板"
category: custom
version: "1.0"
author: "Your Name"
created_at: "2025-08-15"
updated_at: "2025-08-15"

variables:
  role:
    type: string
    required: true
    description: "专业角色"
  
  task:
    type: string
    required: true
    description: "任务描述"
  
  items:
    type: list
    required: true
    description: "输入项目列表"
  
  output_format:
    type: string
    required: false
    default: "JSON"
    description: "输出格式"
```

### 3. 在代码中使用
```python
# 添加到templates.py中的枚举
class PromptTemplate(Enum):
    MY_TEMPLATE = "my_template"

# 使用
prompt = prompt_manager.render_prompt("my_template", variables)
```

## 最佳实践

### ✅ 模板设计原则
1. **清晰的结构**: 使用标题和分段组织内容
2. **详细的说明**: 为AI提供充分的上下文信息
3. **灵活的变量**: 支持可选参数和默认值
4. **输出格式规范**: 明确指定期望的输出格式
5. **质量控制**: 包含质量要求和约束条件

### ✅ 变量命名规范
- 使用下划线命名：`character_name`
- 布尔值用is前缀：`is_default`
- 列表用复数形式：`characters`, `tags`
- 保持一致性：相同类型的变量使用相同命名规则

### ✅ 元数据管理
- 及时更新版本号
- 详细描述变量用途
- 设置合适的类型约束
- 提供使用示例

## 扩展功能

### 🔧 自定义函数
可以为Jinja2环境添加自定义函数：
```python
def custom_filter(value):
    return value.upper()

prompt_manager.jinja_env.filters['upper'] = custom_filter
```

### 🔧 模板继承
支持Jinja2的模板继承功能：
```txt
# base.txt
你是一个专业的{{role}}。
{% block content %}{% endblock %}

# specific.txt
{% extends "base.txt" %}
{% block content %}
请生成{{specific_task}}。
{% endblock %}
```

### 🔧 批量操作
```python
# 批量渲染多个模板
templates = ["template1", "template2", "template3"]
results = []

for template_name in templates:
    result = prompt_manager.render_prompt(template_name, variables)
    results.append(result)
```

## 故障排除

### 常见问题
1. **模板未找到**: 检查文件名和路径
2. **变量验证失败**: 检查变量类型和必需性
3. **渲染错误**: 检查Jinja2语法
4. **权限问题**: 确保文件可读写

### 调试技巧
```python
# 获取模板信息
info = prompt_manager.get_template_info("template_name")
print(info)

# 验证变量
validation = prompt_manager.validate_template("template_name", variables)
print(validation)

# 查看所有模板
templates = prompt_manager.list_templates()
for template in templates:
    print(f"{template['name']}: {template['description']}")
```

## 更新日志

### v1.0 (2025-08-15)
- ✨ 初始版本发布
- ✨ 支持5种基础模板类型
- ✨ 完整的API接口
- ✨ Jinja2模板支持
- ✨ 变量验证功能
- ✨ 元数据管理