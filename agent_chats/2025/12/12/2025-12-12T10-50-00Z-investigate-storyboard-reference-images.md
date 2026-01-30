---
id: 2025-12-12T10-50-00Z-investigate-storyboard-reference-images
date: 2025-12-12T10:50:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, investigation, storyboard]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/services/ai_service_manager.py
summary: "调查分镜参考图未传入问题，确认代码正确实现，识别为网络连接问题"
---

## User Prompt

用户报告：分镜管理，没有传入参考图

提供的日志显示：

```
image_to_image base64 preload failed: All connection attempts failed
```

失败的 URL：

```
http://resource.lets-gpt.com/ai-generated/environments/image/20251211/201751/5ce1b2c0.png
```

## Goals

1. 验证分镜图像生成是否正确传递 reference_images
2. 排查 base64 preload 失败的原因
3. 确认这是代码问题还是环境问题

## Investigation

### 1. 代码路径验证

**前端 → 后端接口**:

- 前端发送 `reference_images` 字段到 `/api/v1/scripts/{script_id}/storyboard/generate-images`
- 后端接口正确提取并传递给 Celery (scripts.py:2224, 2241)

**Celery 任务分发**:

```python
# task_worker.py:89
_process_storyboard_image_task(
    task_id,
    script_id,
    frame_indexes,
    model=payload.get("model"),
    width=int(payload.get("width") or 1024),
    height=int(payload.get("height") or 1024),
    style=payload.get("style") or "realistic",
    reference_images=payload.get("reference_images") or [],  # ✓ 正确传递
)
```

**任务处理函数**:

```python
# scripts.py:2076-2082
# 2) 前端调用时附带的额外参考图（单次请求作用域）
payload_refs = [
    _abs_url(u) for u in (reference_images or []) if isinstance(u, str) and u
]
if payload_refs:
    char_refs.append("用户提供的参考图")
    ref_images_raw.extend(payload_refs)  # ✓ 合并到参考图列表
```

**AI 服务调用**:

```python
# scripts.py:1985-1991
if refs:
    base_image = refs[0]
    extra = refs[1:]
    resp = await ai_service.ai_manager.image_to_image(
        image_url=base_image,
        prompt=prompt,
        model=model_id,
        prefer_provider=prefer_provider,
        count=1,
        extra_images=extra,  # ✓ 正确传递
        width=width,
        height=height,
        style=style,
    )
```

### 2. Base64 预加载机制

**AI Service Manager** (ai_service_manager.py:553-574):

```python
# 预读取参考图，转换为 data:image/...;base64,...，避免外部模型无法访问内网 URL
base64_images: list[str] = []
try:
    urls = [u for u in [image_url] + list(kwargs.get("extra_images") or []) if u]
    if urls:
        async with httpx.AsyncClient(timeout=self.config.default_timeout) as client:
            for url in urls[:14]:
                resp = await client.get(url)
                resp.raise_for_status()
                ctype = resp.headers.get("Content-Type", "image/png")
                subtype = "png"
                if "/" in ctype:
                    subtype = ctype.split("/")[-1] or "png"
                b64 = base64.b64encode(resp.content).decode("ascii")
                base64_images.append(f"data:image/{subtype.lower()};base64,{b64}")
        kwargs["base64_images"] = base64_images
except Exception as e:
    self.logger.warning("image_to_image base64 preload failed: %s", e)
    # ⚠️ 这是一个警告，不是致命错误，图像生成仍会继续
```

**关键发现**：

- Base64 预加载失败只会记录 **warning**，不会导致任务失败
- 图像生成会继续执行，只是可能无法使用预加载的 base64 图像

### 3. 错误原因分析

**症状**：

```
image_to_image base64 preload failed: All connection attempts failed
```

**失败 URL**：

```
http://resource.lets-gpt.com/ai-generated/environments/image/20251211/201751/5ce1b2c0.png
```

**可能原因**：

1. **网络连接问题**：

   - Celery worker 无法访问 `resource.lets-gpt.com`
   - 防火墙或网络策略阻止了连接
   - DNS 解析失败

2. **URL 可访问性**：

   - 该 URL 可能需要 VPN 或特定网络环境
   - 外部域名可能不稳定或已下线

3. **超时配置**：
   - httpx.AsyncClient 使用 `self.config.default_timeout`
   - 如果超时设置过短，可能导致下载失败

## Validation

### 代码验证

✅ **Reference images 传递路径完整**：

- 前端 → 后端接口 ✓
- 后端接口 → Celery payload ✓
- Celery worker → 任务处理函数 ✓
- 任务处理函数 → AI service ✓

✅ **参考图收集逻辑完整** (scripts.py:2063-2106)：

1. 帧级参考图（frame.reference_images）
2. 用户提供的参考图（payload reference_images）
3. 角色锚点图（虚拟 IP 默认图像）
4. 环境参考图（环境资产图像）

### 环境问题确认

❌ **网络连接失败**：

- Worker 无法连接到 `http://resource.lets-gpt.com`
- 这不是代码问题，是环境/网络配置问题

## Conclusion

**代码实现完全正确**，参考图已经正确传递到 AI 服务。

**问题根源**：网络连接问题，Celery worker 无法访问外部资源 URL。

**影响范围**：

- 如果参考图 URL 是外部不可达地址，base64 预加载会失败
- 图像生成会继续，但可能无法利用参考图（取决于 AI provider 是否能直接访问 URL）

## Next Steps

### 1. 用户自查网络配置

检查 Celery worker 是否能访问外部资源：

```bash
docker exec ai-video-celery-worker curl -I http://resource.lets-gpt.com/ai-generated/environments/image/20251211/201751/5ce1b2c0.png
```

如果失败，可能需要：

- 配置 VPN 或代理
- 添加网络路由规则
- 使用内网可访问的图像 URL

### 2. 优化建议（可选）

**方案 A**：增加重试和超时配置

```python
# 增加 httpx 超时时间
async with httpx.AsyncClient(timeout=30.0) as client:
    ...
```

**方案 B**：添加 URL 可达性检查

```python
# 在预加载前先测试 URL 是否可访问
async def is_url_accessible(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.head(url)
            return resp.status_code == 200
    except:
        return False
```

**方案 C**：使用内网镜像

- 将常用的外部参考图下载到本地/OSS
- 使用内网可访问的 URL

### 3. 监控建议

添加监控告警，当 base64 preload 失败率超过阈值时通知运维：

```python
# 在 ai_service_manager.py 中记录 metrics
self.metrics.increment("image_to_image.base64_preload.failed")
```

## Summary

用户报告的"分镜参考图没有传入"实际上是误解：

- ✅ 参考图**已经正确传入**代码
- ❌ Base64 预加载**因网络问题失败**
- ⚠️ 图像生成继续执行，但可能无法利用参考图

**建议用户检查网络配置，确保 Celery worker 能访问外部资源 URL。**
