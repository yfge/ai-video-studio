---
id: 2025-12-12T09-30-00Z-enhance-storyboard-generation-and-config
date: 2025-12-12T09:30:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, frontend, feature, storyboard, config, celery]
related_paths:
  - ai-pic-backend/app/core/config.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/storyboard_reasoner.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/services/providers/base.py
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-frontend/src/app/tasks/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - tasks.md
summary: "增强分镜生成系统，添加 LangGraph 管线支持、配置灵活性和任务管理功能"
---

## User Prompt

提交当前更改（继续之前的开发工作）

## Goals

1. 提交会话开始前已有的开发工作
2. 确保所有更改有适当的文档记录
3. 保持代码库的一致性和可追溯性

## Changes

### 1. 后端配置增强 (config.py, ai_service.py)

**支持 OpenAI 和 Google base URL 配置**：
- 添加 `OPENAI_BASE_URL` 配置项，支持使用 OpenAI 兼容的 API 服务
- 添加 `GOOGLE_BASE_URL` 配置项，支持自定义 Google API 端点
- 默认值分别为 `https://api.openai.com/v1` 和 `https://generativelanguage.googleapis.com`

**优点**：
- 支持使用第三方 OpenAI 兼容服务（如 Azure OpenAI、本地部署的模型等）
- 在受限网络环境中可配置代理或镜像端点
- 便于开发和测试时使用 mock 服务

### 2. 分镜生成系统改进 (storyboard_reasoner.py, ai_service.py)

**StoryboardReActReasoner 重试机制**：
```python
# 允许最多两轮尝试，为"数量不足"场景做一次 ReAct 补救
while attempts < 2 and len(frames_scene_all) < target_frames:
    frames_scene = await self.service.generate_storyboard_from_plan_for_scene(...)
    attempts += 1
    if frames_scene:
        frames_scene_all.extend(frames_scene)
```

**功能特点**：
- 每个场景自动重试最多 2 次，确保达到目标帧数
- 记录详细的重试日志和告警
- 如仍不足，交由上层 fallback 兜底

**LangGraph 管线优先级**：
- `generate_storyboard` 添加 `prefer_graph=True` 参数
- 优先使用 StoryboardReActReasoner 的规划+生成路径
- 保留原有直接生成路径作为 fallback
- 返回完整的 reasoning_trace、plan、fixes 等信息

**JSON Schema 优化**：
- 为 `dialogues`、`stage_directions`、`scenes` 添加明确的 `items` 定义
- 提高 JSON 结构化输出的稳定性

### 3. Celery 任务扩展 (task_worker.py, celery_app.py)

**添加分镜结构生成任务**：
```python
@celery_app.task(name="tasks.storyboard_generate")
def storyboard_generate_task(task_id: int, payload: Dict[str, Any], user_id: int) -> None:
    """异步分镜结构生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_storyboard_generation_task
    _process_storyboard_generation_task(task_id, payload, user_id)
```

**作用**：
- 支持异步生成分镜结构（不含图像）
- 与分镜图像生成任务互补
- 提高大规模分镜生成的响应速度

### 4. 前端任务管理增强 (tasks/page.tsx)

**分页功能**：
- 添加页码和每页大小控制
- 支持总数统计和页面导航
- 改进加载性能，避免一次加载所有任务

**代码优化**：
- 使用 `useCallback` 避免不必要的 `loadTasks` 重建
- 正确处理依赖数组，修复轮询问题

### 5. 前端分镜和剧本页面改进 (episodes/[id]/storyboard/page.tsx, scripts/[id]/page.tsx)

**界面优化**：
- 改进分镜卡片展示
- 优化任务状态显示
- 增强用户交互体验

### 6. 任务规划文档 (tasks.md)

**新增功能规划：分镜 LangGraph 管线统一**

背景：
- 当前分镜生成存在多条路径（直接生成、规划+生成、LangGraph ReAct）
- 前端同时暴露"规划"和"生成"两个操作
- 需要统一为以 LangGraph 为核心的分镜管线

目标：
- 默认走"先规划再生成"路径
- 自动检查帧数量和 JSON 结构合规性
- ReAct 自动修复不足或不合规的情况
- 完整记录 agent 运行轨迹

进度规划：
- [ ] 统一分镜生成模型为 LangGraph 管线
- [ ] 实现/扩展 StoryboardLangGraphAgent
- [ ] 收敛 AIService 和 scripts.py 中的分镜生成逻辑
- [ ] 在分镜 Task 中落库完整 agent 轨迹
- [ ] 前端统一切换到异步路径
- [ ] 补充端到端测试

### 7. Docker 配置更新 (docker-compose.dev.yml)

**Celery 环境变量**：
- 添加必要的环境变量配置
- 确保 Celery worker 能正确访问 AI 服务

### 8. Provider 优化

**Base Provider**：
- 改进错误处理和日志记录
- 统一各 provider 的接口行为

**Google Provider**：
- 支持自定义 base URL
- 改进 API 调用的错误处理

**OpenAI Provider**：
- 支持自定义 base URL
- 优化兼容性

## Validation

1. **语法检查**: Python 和 TypeScript 文件均通过语法检查
2. **配置测试**: 本地验证 OpenAI/Google base URL 配置生效
3. **分镜生成**: 测试重试机制在帧数不足时正常工作
4. **任务管理**: 前端分页功能正常显示和切换

## Next Steps

1. **分镜 LangGraph 管线实现**: 按照 tasks.md 中的规划逐步实现
2. **端到端测试**: 在真实环境中测试完整的分镜生成流程
3. **性能优化**: 监控分镜生成的性能指标，优化重试策略
4. **文档完善**: 更新 API 文档，说明新的配置项和功能

## Linked Commits

待提交：增强分镜生成系统、配置灵活性和任务管理功能
