---
id: 2025-12-10T11-15-00Z-prompt-manager-refactor-plan
date: 2025-12-10T11:15:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, refactor, prompt-management, code-quality]
related_paths:
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/prompts/templates/
  - ai-pic-backend/app/services/ai_service.py
summary: "统一使用提示词管理器管理所有生成业务的提示词"
---

## User Prompt

用户建议将剧本、故事、剧集、分镜等所有生成业务的提示词统一使用提示词管理器管理。

## Goals

1. 统一使用 `prompt_manager` 管理所有提示词
2. 消除 `ai_service.py` 中的硬编码提示词
3. 提高代码的可维护性和一致性
4. 支持提示词的版本管理和A/B测试

## Changes

### 1. 扩展 PromptTemplate 枚举 (app/prompts/templates.py)

**新增模板类型**：

```python
# 剧集相关
EPISODE_LIST = "episode_list"  # 剧集列表生成

# 场景和分镜相关
SCENE_DESCRIPTION = "scene_description"  # 场景描述
STORYBOARD_GENERATION = "storyboard_generation"  # 分镜生成
STORYBOARD_SHOT = "storyboard_shot"  # 单个分镜画面

# 图像相关
ENVIRONMENT_IMAGE = "environment_image"  # 环境图像

# 系统提示词
SYSTEM_PROMPT_STORY = "system_prompt_story"  # 故事创作系统提示
SYSTEM_PROMPT_SCRIPT = "system_prompt_script"  # 剧本创作系统提示
SYSTEM_PROMPT_JSON_STRICT = "system_prompt_json_strict"  # 严格JSON系统提示
```

### 2. 创建新的模板文件

创建了以下模板文件：

- `system_prompt_story.txt` - 故事创作系统提示词
- `system_prompt_script.txt` - 剧本创作系统提示词
- `system_prompt_json_strict.txt` - 严格JSON系统提示词
- `episode_list.txt` - 剧集列表生成模板
- `storyboard_generation.txt` - 分镜生成模板
- `environment_image.txt` - 环境图像生成模板

### 3. 待重构的代码位置 (ai_service.py)

#### 3.1 故事概要生成 (line 433)

**当前代码**：

```python
system_prompt="你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据用户的要求生成高质量的故事内容。"
```

**重构后**：

```python
system_prompt=prompt_manager.render_prompt(
    PromptTemplate.SYSTEM_PROMPT_STORY.value, {}
)
```

#### 3.2 故事概要重试 (line 459)

**当前代码**：

```python
system_prompt="你是一个专业的编剧和故事创作者，返回内容必须是严格的JSON，符合提供的Schema。"
```

**重构后**：

```python
system_prompt=prompt_manager.render_prompt(
    PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
)
```

#### 3.3 剧集规划生成 (line 678, 696)

**当前代码**：

```python
system_prompt="你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据用户的要求生成高质量的剧集规划。"
```

**重构后**：

```python
system_prompt=prompt_manager.render_prompt(
    PromptTemplate.SYSTEM_PROMPT_SCRIPT.value, {}
)
```

#### 3.4 剧集列表生成 (line 735)

**当前代码**：

```python
prompt = f"""你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成{episode_count}集的剧集大纲：

## 故事信息
故事标题：{story.get('title', '未命名故事')}
类型：{story.get('genre', '剧情')}
故事概要：{story.get('synopsis', '暂无概要')}
...
```

**重构后**：

```python
prompt = prompt_manager.render_prompt(
    PromptTemplate.EPISODE_LIST.value,
    {
        "episode_count": episode_count,
        "story": story,
        "total_duration_minutes": total_duration_minutes,
        "episode_duration": episode_duration
    }
)
```

#### 3.5 fallback 系统提示 (line 1500)

**当前代码**：

```python
{
    "role": "system",
    "content": "你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据用户的要求生成高质量的故事内容。",
}
```

**重构后**：

```python
{
    "role": "system",
    "content": prompt_manager.render_prompt(
        PromptTemplate.SYSTEM_PROMPT_STORY.value, {}
    ),
}
```

## Implementation Steps

### Phase 1: 准备工作 ✅

1. ✅ 扩展 PromptTemplate 枚举
2. ✅ 创建系统提示词模板文件
3. ✅ 创建新的业务模板文件
4. ✅ 更新模板分类映射

### Phase 2: 重构 ai_service.py (下一步)

1. ⏳ 替换所有硬编码的系统提示词
2. ⏳ 替换剧集列表生成提示词
3. ⏳ 测试所有修改的功能
4. ⏳ 创建提示词使用文档

### Phase 3: 优化和清理 (未来)

1. ⏳ 检查其他服务文件中的硬编码提示词
2. ⏳ 添加提示词版本管理
3. ⏳ 实现提示词A/B测试框架
4. ⏳ 添加提示词效果监控

## Benefits

1. **统一管理**：所有提示词在一个地方管理，便于维护
2. **版本控制**：提示词变更可以通过Git跟踪
3. **可测试性**：可以轻松测试不同版本的提示词效果
4. **国际化支持**：未来可以轻松添加多语言支持
5. **模板复用**：提示词可以在不同场景中复用
6. **代码整洁**：消除大量硬编码字符串，提高代码可读性

## Example Usage

### Before (硬编码)

```python
system_prompt = "你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据用户的要求生成高质量的故事内容。"
```

### After (使用 prompt_manager)

```python
system_prompt = prompt_manager.render_prompt(
    PromptTemplate.SYSTEM_PROMPT_STORY.value,
    {}
)
```

### 带变量的模板

```python
prompt = prompt_manager.render_prompt(
    PromptTemplate.EPISODE_LIST.value,
    {
        "episode_count": 10,
        "story": story_data,
        "total_duration_minutes": 300,
        "episode_duration": 30
    }
)
```

## Next Steps

1. 继续重构 ai_service.py 中的其他硬编码提示词
2. 运行完整的测试套件验证功能正常
3. 更新相关文档
4. 提交重构changes

## References

- 提示词管理器文档: `app/prompts/README.md`
- 模板定义: `app/prompts/templates.py`
- 模板文件目录: `app/prompts/templates/`
