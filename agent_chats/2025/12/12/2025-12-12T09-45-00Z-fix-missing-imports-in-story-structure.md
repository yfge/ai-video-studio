---
id: 2025-12-12T09-45-00Z-fix-missing-imports-in-story-structure
date: 2025-12-12T09:45:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, bugfix, hotfix]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "修复 story_structure.py 缺失的导入，解决环境图生图异步任务运行时错误"
---

## User Prompt

用户提供了运行时错误日志：

```
NameError: name 'ai_service' is not defined
```

错误发生在 `story_structure.py:731` 的 `generate_environment_image_variants_async` 函数中。

## Goals

1. 快速定位并修复运行时错误
2. 确保环境图生图异步任务能正常运行
3. 验证修复不引入新问题

## Changes

### 问题分析

在之前修复环境资产图生图时 (commit: `364b5b7`)，我们在 `story_structure.py` 中使用了以下未导入的模块：

- `ai_service` (line 320, 433, 507, 592, 644, 686, 731, 850)
- `oss_service` (line 331)
- `environment_image_variant_task` (line 781)

但忘记在文件开头添加相应的 import 语句。

### 根本原因

在修复过程中，参考了 `virtual_ip_images.py` 的实现，但没有同步检查其导入语句。`virtual_ip_images.py` 在第 18-20 行正确导入了：

```python
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.services.task_worker import (
    virtual_ip_image_generate_task,
    virtual_ip_image_variant_task,
)
```

### 修复实施

在 `story_structure.py` 的导入部分添加缺失的 import 语句：

```python
from app.services import story_structure_service as svc
from app.services.ai_service import ai_service          # 新增
from app.services.storage import oss_service            # 新增
from app.services.task_worker import environment_image_variant_task  # 新增
from app.models.task import Task, TaskStatus, TaskType
```

## Validation

1. **语法检查**: ✓ `python -m py_compile` 通过
2. **导入检查**: 确认所有使用的模块都已正确导入
3. **运行时验证**: 待用户重启服务后测试环境图生图功能

## Next Steps

1. **重启服务**: 用户需要重启后端服务使修复生效
2. **功能测试**: 重新测试环境图生图异步任务
3. **代码审查**: 检查是否有其他文件存在类似问题

## Linked Commits

待提交：修复 story_structure.py 缺失的导入语句
