---
id: 2025-12-12T08-30-00Z-fix-reference-images-in-virtual-ip-img2img
date: 2025-12-12T08:30:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, frontend, bugfix, image-generation, celery]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
summary: "修复虚拟IP图生图异步任务缺少参考图传递的问题"
---

## User Prompt

用户反馈：目前文图生图的异步任务里没有把参考图真正的传进去，仔细排查一下

## Goals

1. 排查虚拟IP图生图异步任务中参考图传递的完整链路
2. 识别前端和后端代码中缺失参考图传递的位置
3. 参考已正确实现的分镜图像任务，修复虚拟IP图生图任务
4. 确保从前端到后端 worker 的完整传递链路正确

## Changes

### 问题分析

通过对比分镜图像任务（已正确实现参考图传递）和虚拟IP图生图任务，发现以下缺失：

1. **前端 API** (`ai-pic-frontend/src/utils/api.ts:2029-2049`)

   - `generateVariantAndSaveAsync` 函数只传递了 `prompt`, `model`, `count`, `size`
   - **缺失**: `reference_images` 参数未包含在 TypeScript 类型和请求体中

2. **前端页面** (`ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx:340-348`)

   - `handleSubmitVariant` 收到了 `payload.referenceImages` 参数
   - **缺失**: 未将该参数传递给 API 调用

3. **后端接口** (`ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py:768-801`)

   - `generate_virtual_ip_image_variant_async` 从请求中提取参数
   - **缺失**: 未提取 `reference_images` 并加入 payload

4. **后端 Worker** (`ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py:1018-1045`)
   - `_process_virtual_ip_image_variant_task` 调用 `ai_manager.image_to_image`
   - **缺失**: 未从 payload 提取 `reference_images` 并通过 `extra_images` 传递

### 修复实施

#### 1. 前端 TypeScript 类型定义 (api.ts:165-173)

```typescript
export interface ImageToImageRequestPayload {
  image_url: string;
  prompt?: string;
  model?: string;
  prefer_provider?: string;
  count?: number;
  size?: string;
  reference_images?: string[]; // 新增
}
```

#### 2. 前端 API 函数 (api.ts:2029-2050)

```typescript
generateVariantAndSaveAsync: async (
  virtualIPId: number,
  imageId: number,
  payload: Pick<
    ImageToImageRequestPayload,
    "prompt" | "model" | "count" | "size" | "reference_images"  // 新增
  >,
): Promise<ApiResponse<{ task_id: number; status: string }>> => {
  return apiClient.makeRequest(
    `/api/v1/virtual-ips/${virtualIPId}/images/${imageId}/variants-async`,
    {
      method: "POST",
      body: JSON.stringify({
        prompt: payload.prompt,
        model: payload.model,
        count: payload.count ?? 1,
        size: payload.size,
        reference_images: payload.reference_images,  // 新增
      }),
    },
  );
},
```

#### 3. 前端页面调用 (page.tsx:340-350)

```typescript
const res = await virtualIPImageAPI.generateVariantAndSaveAsync(
  virtualIPId,
  variantTarget.id,
  {
    prompt: payload.prompt || variantPrompt,
    model: modelFallback || undefined,
    count: payload.count,
    size: payload.size || generateForm.size,
    reference_images: payload.referenceImages, // 新增
  },
);
```

#### 4. 后端接口提取参数 (virtual_ip_images.py:782,800)

```python
reference_images_value = payload_body.get("reference_images") or []

# 组装 payload
payload: Dict[str, Any] = {
    "virtual_ip_id": virtual_ip_id,
    "image_id": image_id,
    "prompt": prompt_value,
    "model": selected_model,
    "count": count_int,
    "size": size_value,
    "reference_images": reference_images_value,  # 新增
}
```

#### 5. 后端 Worker 传递给 AI 服务 (virtual_ip_images.py:1021-1045)

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
    model=selected_model or None,
    prefer_provider=prefer_provider,
    count=count_int,
    size=size_value,
    extra_images=extra_images,  # 新增
)
```

## Validation

1. **前端 lint 检查**: ✓ 通过（仅有无关的 eslint-disable 警告）
2. **后端语法检查**: ✓ 通过 (`python -m py_compile`)
3. **代码结构对比**: 与已实现的分镜图像任务保持一致
   - 分镜任务参考: `task_worker.py:89`, `scripts.py:1991`
   - 虚拟IP任务现已对齐
4. **AI服务管理器验证**: `ai_service_manager.py:553-574` 确认支持 `extra_images` 参数
   - 参数通过 `kwargs` 传递
   - 内部自动转换为 base64 格式 (`base64_images`)

## Next Steps

1. **人工测试**: 需要在真实环境中验证虚拟IP图生图功能

   - 使用测试账号 `geyunfei` / `Gyf@845261`
   - 在虚拟IP图像页选择一张图执行图生图
   - 确认前端选中的参考图正确传递到后端
   - 验证 Celery worker 日志中包含 reference_images 信息
   - 检查生成的图像是否受参考图影响

2. **后续优化**:

   - 考虑为环境图生图任务添加同样的参考图支持（目前也缺失）
   - 统一所有图生图接口的参数处理逻辑

3. **文档更新**: 在 API 文档中标注参考图参数为可选

## Linked Commits

待提交：修复虚拟IP图生图异步任务中参考图传递
