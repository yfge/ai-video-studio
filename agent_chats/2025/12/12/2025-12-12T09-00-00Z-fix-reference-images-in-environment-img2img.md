---
id: 2025-12-12T09-00-00Z-fix-reference-images-in-environment-img2img
date: 2025-12-12T09:00:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, frontend, bugfix, image-generation, celery]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "修复环境资产图生图异步任务缺少参考图传递的问题"
---

## User Prompt

用户继续反馈：修复环境资产和分镜管理中的图文生图的问题

## Goals

1. 排查环境资产图生图异步任务中参考图传递的完整链路
2. 对比虚拟IP图生图（已修复）和分镜图像生成（已正确实现），修复环境资产图生图
3. 确认分镜管理的图生图任务是否需要修复
4. 确保从前端到后端 worker 的完整传递链路正确

## Changes

### 问题分析

**环境资产图生图** 与虚拟IP图生图存在相同的问题：

1. **前端页面** (`ai-pic-frontend/src/app/environments/page.tsx:158`)
   - `handleGenerateVariant` 接收到了 `payload.referenceImages` (ImageToImageModal 传递)
   - **缺失**: 未将该参数传递给 API 调用

2. **前端 API** (`ai-pic-frontend/src/utils/api.ts:1266-1285`)
   - `generateEnvironmentImageVariantsAsync` 类型定义和请求体
   - **缺失**: `reference_images` 参数未包含在类型和请求中

3. **后端接口** (`ai-pic-backend/app/api/v1/endpoints/story_structure.py:712-780`)
   - `generate_environment_image_variants_async` 从请求中提取参数
   - **缺失**: 未提取 `reference_images` 并加入 payload

4. **后端 Worker** (`ai-pic-backend/app/api/v1/endpoints/story_structure.py:783-863`)
   - `_process_environment_image_variant_task` 调用 `ai_manager.image_to_image`
   - **缺失**: 未从 payload 提取 `reference_images` 并通过 `extra_images` 传递

**分镜管理图生图** 已正确实现：
- 后端接口 `generate_storyboard_images` (scripts.py:2223,2240) 正确传递 `reference_images`
- task_worker.py:89 正确从 payload 提取并传递给处理函数
- **无需修复**

### 修复实施

#### 1. 前端页面接收参数 (environments/page.tsx:158)

```typescript
const handleGenerateVariant = async (payload: {
  prompt: string;
  model?: string;
  count: number;
  size?: string;
  referenceImages: string[]  // 新增
}) => {
  // ...
  const res = await storyStructureAPI.generateEnvironmentImageVariantsAsync(variantTarget.env.id, {
    base_image: variantTarget.url,
    prompt: payload.prompt || variantPrompt,
    model: payload.model || variantTarget.modelHint,
    size: payload.size,
    count: payload.count,
    reference_images: payload.referenceImages,  // 新增
  })
}
```

#### 2. 前端 API 类型和传递 (api.ts:1266-1285)

```typescript
async generateEnvironmentImageVariantsAsync(
  envId: number,
  payload: {
    base_image?: string;
    prompt?: string;
    model?: string;
    count?: number;
    size?: string;
    style?: string;
    reference_images?: string[];  // 新增
  },
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  // ...
}
```

#### 3. 后端接口提取参数 (story_structure.py:750,765)

```python
reference_images_value = body.get("reference_images") or []

payload = {
    "env_id": env_id,
    "base_image": base,
    "model": model_raw,
    "count": count_int,
    "size": size_value,
    "style": style_hint,
    "prompt": extra_prompt,
    "reference_images": reference_images_value,  # 新增
}
```

#### 4. 后端 Worker 传递给 AI 服务 (story_structure.py:834-858)

```python
# 提取参考图并转换为绝对 URL
reference_images = payload.get("reference_images") or []
extra_images = []
for ref_url in reference_images:
    if not ref_url:
        continue
    if ref_url.startswith("http"):
        extra_images.append(ref_url)
    else:
        # 转换相对路径为绝对 URL
        path = ref_url if ref_url.startswith("/") else f"/{ref_url}"
        backend_base = (
            getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
        ).rstrip("/")
        extra_images.append(f"{backend_base}{path}")

response = await ai_service.ai_manager.image_to_image(
    image_url=image_url,
    prompt=prompt_value,
    model=model_value,
    prefer_provider=prefer_provider,
    count=max(1, min(count_int, 4)),
    size=size_value,
    style=style_hint_local,
    extra_images=extra_images,  # 新增
)
```

## Validation

1. **前端 lint 检查**: ✓ 通过（仅有无关的 eslint-disable 警告）
2. **后端语法检查**: ✓ 通过 (`python -m py_compile`)
3. **分镜任务确认**: ✓ 已正确实现，无需修复
4. **代码结构对比**: 与虚拟IP图生图修复保持一致

## Next Steps

1. **人工测试**: 需要在真实环境中验证环境资产图生图功能
   - 使用测试账号 `geyunfei` / `Gyf@845261`
   - 在环境资产页面选择一张环境图执行图生图
   - 确认前端选中的参考图正确传递到后端
   - 验证 Celery worker 日志中包含 reference_images 信息
   - 检查生成的环境图是否受参考图影响

2. **一致性审查**: 检查其他可能存在类似问题的图生图接口

3. **文档更新**: 更新 API 文档，标注所有图生图接口的参考图参数

## Linked Commits

待提交：修复环境资产图生图异步任务中参考图传递
