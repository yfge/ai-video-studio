---
id: 2025-12-12T11-00-00Z-fix-virtual-ip-variant-missing-reference-images
date: 2025-12-12T11:00:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [frontend, bugfix, virtual-ip]
related_paths:
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
summary: "修复虚拟IP图生图前端未传递 reference_images 参数"
---

## User Prompt

用户报告：虚拟IP图生图还是有问题

查看 Celery worker 日志后发现：

```
[2025-12-11 20:27:23,409: INFO/ForkPoolWorker-8] HTTP Request: GET http://ai-video-backend:8000/uploads/c74780f913784235acd5e548886c1ef8.png "HTTP/1.1 200 OK"
[2025-12-11 20:27:23,417: WARNING/ForkPoolWorker-8] image_to_image base64 preload failed: All connection attempts failed
```

只下载了一张图片（base image），没有参考图。

## Goals

1. 找到虚拟IP图生图参考图未传递的原因
2. 修复前端传参问题
3. 验证修复后参考图能正确传递

## Problem Analysis

### 症状

Celery 日志显示：

- 只下载了 base image，没有下载 reference images
- "All connection attempts failed" 错误信息误导（实际上是因为 extra_images 列表为空）

### 根本原因

前端代码 `page.tsx:322-350` 的 `handleSubmitVariant` 函数：

**接收了 `referenceImages` 参数**（line 328）：

```typescript
const handleSubmitVariant = async (payload: {
  prompt: string;
  model?: string;
  count: number;
  size?: string;
  style?: string;
  referenceImages: string[];  // ✓ 接收了
}) => {
```

**但没有传给 API**（line 340-347）：

```typescript
const res = await virtualIPImageAPI.generateVariantAndSaveAsync(
  virtualIPId,
  variantTarget.id,
  {
    prompt: payload.prompt || variantPrompt,
    model: modelFallback || undefined,
    count: payload.count,
    size: payload.size || generateForm.size,
    // ❌ 缺少 reference_images: payload.referenceImages
  },
);
```

### 为什么之前没发现

1. **后端代码正确**：所有后端传递链路都已实现（接口 → Celery → worker → AI service）
2. **前端遗漏**：只有这一处忘记传参
3. **测试盲点**：可能没有实际使用参考图功能进行端到端测试

## Changes

### 修复位置

`ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx:348`

**修改前**：

```typescript
const res = await virtualIPImageAPI.generateVariantAndSaveAsync(
  virtualIPId,
  variantTarget.id,
  {
    prompt: payload.prompt || variantPrompt,
    model: modelFallback || undefined,
    count: payload.count,
    size: payload.size || generateForm.size,
  },
);
```

**修改后**：

```typescript
const res = await virtualIPImageAPI.generateVariantAndSaveAsync(
  virtualIPId,
  variantTarget.id,
  {
    prompt: payload.prompt || variantPrompt,
    model: modelFallback || undefined,
    count: payload.count,
    size: payload.size || generateForm.size,
    reference_images: payload.referenceImages, // ✓ 新增
  },
);
```

## Validation

### 1. 语法检查

```bash
cd ai-pic-frontend && npm run lint
```

✅ 通过（只有无关的 eslint-disable 警告）

### 2. 完整传递链路确认

**前端 → API**：

- `ImageToImageModal` 收集 `referenceImages` ✓
- `handleSubmitVariant` 接收 `payload.referenceImages` ✓
- **现在传给 API** `reference_images: payload.referenceImages` ✅（已修复）

**API → 后端 → Celery → Worker → AI Service**：

- `api.ts` 类型定义包含 `reference_images` ✓
- 后端接口提取 `payload.get("reference_images")` ✓
- Celery payload 包含 `reference_images` ✓
- Worker 提取并转换为绝对 URL ✓
- 传给 AI service 的 `extra_images` ✓

## Next Steps

### 1. 重启前端开发服务器

```bash
cd ai-pic-frontend
npm run dev
```

### 2. 端到端测试

1. 打开虚拟IP图像管理页面
2. 选择一张基础图像，点击"图生图"
3. 在 `ImageToImageModal` 中：
   - 添加参考图（选择其他虚拟IP图像）
   - 输入提示词
   - 提交
4. 检查 Celery worker 日志：

   ```bash
   docker logs -f ai-video-celery-worker
   ```

   应该看到多个 `HTTP Request: GET` 日志，对应每张参考图

5. 检查生成的图像是否体现了参考图的特征

### 3. 相关检查

确认以下页面也正确传递了 `reference_images`：

- ✅ 环境资产图生图（`environments/page.tsx`）- 已在之前修复
- ✅ 分镜图像生成（`scripts.py`）- 后端已正确实现

## Linked Commits

待提交：修复虚拟IP图生图前端未传递 reference_images 参数
