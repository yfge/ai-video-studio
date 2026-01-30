---
id: 2025-12-12T10-00-00Z-fix-missing-model-utils-imports
date: 2025-12-12T10:00:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, bugfix, hotfix]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "修复 story_structure.py 缺失的工具函数导入，解决环境图生图任务失败"
---

## User Prompt

用户反馈：环境图生图任务显示成功，但实际上没有生成图片。

## Goals

1. 排查环境图生图任务实际执行状态
2. 找到真正的失败原因
3. 修复问题确保任务能正常完成

## Changes

### 问题分析

通过检查数据库中的任务状态，发现：

```python
Task ID: 127
Status: TaskStatus.FAILED
Result: None
Error: name 'parse_model_and_provider' is not defined
```

**实际情况**：

- Celery worker 日志显示任务 "succeeded"，但这只是指任务执行完成，不代表业务逻辑成功
- 数据库中的任务状态是 FAILED
- 真正的错误是：`name 'parse_model_and_provider' is not defined`

**根本原因**：
在 `_process_environment_image_variant_task` (line 819) 中使用了以下工具函数：

- `parse_model_and_provider` (line 670, 819)
- `normalize_openai_image_style` (line 462, 589, 674, 825)

这两个函数定义在 `app.utils.model_utils` 中，但在 story_structure.py 中没有导入。

### 为什么之前没发现

1. **同步路径正常**：同步的环境图生图接口 (line 670) 使用了这些函数，但由于是在主进程中执行，可能由于某种原因能访问到（或者那条路径没有被测试）
2. **异步路径失败**：Celery worker 在独立进程中运行，作用域隔离更严格，导致这个问题暴露
3. **日志误导**：Celery 的 "succeeded" 日志只表示任务函数执行完成，不检查业务逻辑是否成功

### 修复实施

在 `story_structure.py` 的导入部分添加缺失的工具函数：

```python
from app.core.config import settings
from app.utils.model_utils import parse_model_and_provider, normalize_openai_image_style
```

## Validation

1. **语法检查**: ✓ `python -m py_compile` 通过
2. **函数使用检查**: 确认所有使用位置都已覆盖
   - `parse_model_and_provider`: line 670, 819
   - `normalize_openai_image_style`: line 462, 589, 674, 825
3. **运行时验证**: 待用户重启服务后重试环境图生图

## Next Steps

1. **重启服务**: 用户需要重启 Celery worker 使修复生效

   ```bash
   docker-compose restart ai-video-celery-worker
   ```

2. **重试任务**: 在环境资产页面重新执行图生图

3. **验证结果**: 检查：

   - Task 状态变为 COMPLETED
   - 环境资产的 reference_images 列表增加了新图片
   - 前端页面刷新后能看到新图片

4. **代码审查**: 检查其他异步任务处理函数是否有类似问题

## Lessons Learned

1. **导入检查清单**: 在添加新的异步任务处理函数时，确保所有使用的函数都已导入
2. **日志理解**: Celery 的 "succeeded" 不等于业务成功，需要检查数据库中的实际状态
3. **测试覆盖**: 异步任务需要端到端测试，不能只依赖语法检查

## Linked Commits

待提交：修复 story_structure.py 缺失的 model_utils 工具函数导入
