---
id: 2025-12-12T11-15-00Z-deploy-virtual-ip-reference-images-fix
date: 2025-12-12T11:15:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [deployment, frontend, verification]
related_paths:
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - docker/docker-compose.dev.yml
summary: "部署虚拟IP图生图参考图修复，重启前端容器"
---

## User Prompt

用户要求先处理虚拟IP图生图的问题。

Celery 日志确认问题：
```
HTTP Request: GET http://ai-video-backend:8000/uploads/edac679d41a1488aa6521b439bc270e1.png "HTTP/1.1 200 OK"
image_to_image base64 preload failed: All connection attempts failed
```

只下载了一张图片（base image），证明 `extra_images` 为空，参考图没有传递。

## Goals

1. 部署已修复的前端代码
2. 验证修复是否生效
3. 确认参考图能正确传递到 AI 服务

## Changes

### 已修复代码（Commit c46e35f）

`ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx:348`

添加了缺失的参数：
```typescript
const res = await virtualIPImageAPI.generateVariantAndSaveAsync(
  virtualIPId,
  variantTarget.id,
  {
    prompt: payload.prompt || variantPrompt,
    model: modelFallback || undefined,
    count: payload.count,
    size: payload.size || generateForm.size,
    reference_images: payload.referenceImages,  // ✅ 新增
  },
);
```

### 部署步骤

1. **重启前端容器**：
   ```bash
   docker-compose -f docker/docker-compose.dev.yml restart ai-video-frontend
   ```

2. **验证启动**：
   ```bash
   docker logs --tail 20 ai-video-frontend
   ```

   确认看到：
   ```
   ▲ Next.js 15.4.1
   - Local:        http://localhost:3000
   - Network:      http://0.0.0.0:3000
   ✓ Ready in 2.1s
   ```

## Validation

### 预期修复效果

**修复前** Celery 日志：
```
HTTP Request: GET http://ai-video-backend:8000/uploads/<base>.png "HTTP/1.1 200 OK"
image_to_image base64 preload failed: All connection attempts failed
```
↑ 只下载一张图片

**修复后** 预期 Celery 日志：
```
HTTP Request: GET http://ai-video-backend:8000/uploads/<base>.png "HTTP/1.1 200 OK"
HTTP Request: GET http://ai-video-backend:8000/uploads/<ref1>.png "HTTP/1.1 200 OK"
HTTP Request: GET http://ai-video-backend:8000/uploads/<ref2>.png "HTTP/1.1 200 OK"
...
```
↑ 下载 base image + 所有 reference images

### 手动测试步骤

1. **访问虚拟IP图像管理页面**：
   ```
   http://localhost:3000/virtual-ip/{id}/images
   ```

2. **选择一张图片，点击"图生图"图标**

3. **在 ImageToImageModal 中**：
   - 添加 1-3 张参考图（从图像列表中选择）
   - 输入提示词（如"生成全身照"）
   - 选择模型（如 `volcengine:seedream-4.5`）
   - 提交

4. **监控 Celery 日志**：
   ```bash
   docker logs -f ai-video-celery-worker
   ```

5. **验证点**：
   - ✅ 看到多个 `HTTP Request: GET` 日志（base + references）
   - ✅ 看到 `base64_images` 包含多张图片
   - ✅ AI provider 收到完整的参考图列表
   - ✅ 生成的图像体现了参考图的特征

### 自动化验证（可选）

使用 Chrome DevTools Protocol 自动化测试（通过 MCP）：

```javascript
// 1. 登录
// 2. 导航到虚拟IP图像页面
// 3. 模拟点击图生图
// 4. 选择参考图
// 5. 提交
// 6. 检查网络请求 payload 是否包含 reference_images
```

## Next Steps

### 1. 用户测试

请用户执行手动测试步骤，验证：
- 前端是否正确发送 `reference_images` 参数
- 后端是否收到并转发给 AI 服务
- Celery 日志是否显示下载多张图片

### 2. 如果仍有问题

检查点：
- 前端请求 payload 是否包含 `reference_images`（浏览器 DevTools Network 面板）
- 后端日志是否收到 `reference_images`
- Worker 日志中 `extra_images` 列表长度

### 3. 分镜管理问题

虚拟IP图生图验证通过后，再处理分镜管理的参考图问题。

## Status

- ✅ 前端代码已修复（commit c46e35f）
- ✅ 前端容器已重启
- ⏳ 等待用户测试验证

## Linked Commits

- c46e35f: fix(frontend): pass reference_images in virtual IP variant request
