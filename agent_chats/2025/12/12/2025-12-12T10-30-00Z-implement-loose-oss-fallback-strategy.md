---
id: 2025-12-12T10-30-00Z-implement-loose-oss-fallback-strategy
date: 2025-12-12T10:30:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, enhancement, oss, reliability]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "实施宽松OSS兜底策略，提高异步任务成功率"
---

## User Prompt

用户询问：检查一下异步任务里用oss兜底了么？

在分析后，用户选择了方案 A：宽松兜底（推荐）策略。

## Goals

1. 分析当前异步任务中的 OSS 上传策略
2. 实施宽松兜底策略，提高任务成功率
3. 确保所有图像生成相关接口（同步/异步）保持一致

## Changes

### 问题分析

**当前策略**（修改前）：
```python
require_upload=bool(oss_service)
```

**行为**：
- OSS 未配置：使用本地存储 ✅
- OSS 已配置 + 上传成功：使用 OSS URL ✅
- OSS 已配置 + 上传失败：任务失败 ❌

**风险**：
- 如果 OSS 临时不可用（网络问题、服务故障等），任务完全失败
- 即使本地文件已下载成功，也会浪费 AI 调用额度
- 用户需要重新提交任务

### 解决方案：宽松兜底策略

**新策略**：
```python
require_upload=False
```

在 `AIService._persist_local_image` 中的逻辑：
```python
if oss_service:
    try:
        # 尝试上传到 OSS
        oss_result = await self._upload_local_image_to_oss(...)
        oss_url = oss_result.get("file_url")
    except Exception as exc:
        if require_upload:
            raise  # require_upload=True 时，抛出异常
        # require_upload=False 时，记录警告，继续使用本地路径
        self.logger.warning("OSS 上传失败，使用本地路径: %s", exc)
```

**新行为**：
- OSS 未配置：使用本地存储 ✅
- OSS 已配置 + 上传成功：使用 OSS URL ✅
- OSS 已配置 + 上传失败：兜底到本地存储 ✅（新增）

### 修改位置

共修改 5 处，覆盖所有图像生成相关接口：

1. **virtual_ip_images.py:84** - 用户上传虚拟IP图像
   ```python
   # 宽松兜底：OSS 上传失败时自动回退到本地存储
   require_upload=False,
   ```

2. **virtual_ip_images.py:683** - 同步虚拟IP图生图
   ```python
   # 宽松兜底：OSS 上传失败时自动回退到本地存储
   require_upload=False,
   ```

3. **virtual_ip_images.py:1072** - 异步虚拟IP图生图
   ```python
   # 宽松兜底：OSS 上传失败时自动回退到本地存储，确保任务成功
   require_upload=False,
   ```

4. **story_structure.py:334** - 环境图生成（同步+异步共用）
   ```python
   # 宽松兜底：OSS 上传失败时自动回退到本地存储，确保任务成功
   require_upload=False,
   ```

5. **scripts.py:2042** - 分镜图像生成（异步）
   ```python
   # 宽松兜底：OSS 上传失败时自动回退到本地存储，确保任务成功
   require_upload=False,
   ```

## Benefits

1. **任务成功率提升**：OSS 临时故障不会导致整个任务失败
2. **用户体验改善**：图片至少能在本地看到，不需要重新生成
3. **成本节约**：避免因 OSS 问题重复消耗 AI 调用额度
4. **渐进式降级**：优先使用 OSS，失败时自动降级到本地存储
5. **统一策略**：所有接口（同步/异步）行为一致

## Trade-offs

**潜在缺点**：
- 部分图片可能只在本地，没有 OSS 备份
- 需要确保本地存储空间充足

**缓解措施**：
- `_persist_local_image` 会记录警告日志，便于监控 OSS 上传失败率
- 可以实现后台任务定期重试上传失败的图片
- 监控告警可以及时发现 OSS 持续性问题

## Validation

1. **语法检查**: ✓ 所有修改的文件通过语法检查
2. **修改确认**: ✓ 共 5 处修改，覆盖所有图像生成接口
3. **逻辑验证**: ✓ `_persist_local_image` 逻辑支持宽松兜底

## Next Steps

1. **重启服务**: 使修改生效
   ```bash
   docker-compose restart ai-video-backend ai-video-celery-worker
   ```

2. **监控验证**: 观察 OSS 上传失败率
   - 检查日志中的 "OSS 上传失败，使用本地路径" 警告
   - 确认任务不会因 OSS 问题而失败

3. **后续优化**（可选）:
   - 实现后台重试机制，定期尝试上传只有本地路径的图片
   - 添加 Prometheus metrics 监控 OSS 上传成功率
   - 考虑添加配置项 `OSS_FALLBACK_ENABLED` 用于禁用兜底（如果需要严格要求 OSS）

## Linked Commits

待提交：实施宽松OSS兜底策略，提高图像生成任务可靠性
