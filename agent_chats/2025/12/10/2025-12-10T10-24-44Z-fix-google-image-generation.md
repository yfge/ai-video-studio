---
id: 2025-12-10T10-24-44Z-fix-google-image-generation
date: 2025-12-10T10:24:44Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, google, image-generation, bug-fix]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-backend/tests/unit/test_google_provider_image.py
summary: "修复 Google Gemini 图像生成 API 调用失败问题：更正 base_url 和添加必需的 responseModalities 配置"
---

## User Prompt

处理 Google Gemini 图像生成失败错误：

```
ai-video-backend | 2025-12-10T17:54:30.203+08:00 [INFO] LLM Response | task=generate_image provider=google model=gemini-3-pro-image-preview status=failure usage={} body=None
ai-video-backend | 2025-12-10T17:54:30.205+08:00 [ERROR] AI管理器图像生成失败: 所有图像生成提供商都失败了
```

## Goals

1. 识别 Google 图像生成 API 调用失败的根本原因
2. 改进错误日志以显示详细错误信息
3. 修复 API 配置问题
4. 确保测试覆盖新的修复
5. 验证修复在实际环境中工作

## Changes

### 1. 改进错误日志 (ai-pic-backend/app/services/ai_service_manager.py:97-111)

**修改前**：失败时只显示 `body=None`，无法定位具体错误

**修改后**：

```python
def _log_response(self, *, task: str, provider: Optional[str], model: Optional[str], response: AIResponse):
    try:
        status = "success" if (response and response.success) else "failure"
        if response and not response.success and response.error:
            body_preview = f"ERROR: {self._truncate(response.error, 2000)}"
        else:
            body_preview = self._truncate(response.data if response else None, 2000)
        # ... 其余代码
```

改进后的日志显示了具体错误：

```
ERROR: google 错误: Client error '404 Not Found' for url 'https://aiplatform.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent'
```

### 2. 修复 Google API Base URL (ai-pic-backend/app/services/ai_service.py:314-315)

**问题**：使用了错误的 Vertex AI endpoint

**修改前**：

```python
base_url="https://aiplatform.googleapis.com",
```

**修改后**：

```python
# 使用 Generative Language API (不是 Vertex AI)
base_url="https://generativelanguage.googleapis.com",
```

**原因**：图像生成应使用 Generative Language API，而非 Vertex AI endpoint

### 3. 添加必需的 responseModalities 配置 (ai-pic-backend/app/services/providers/google_provider.py)

**问题**：根据 Google 官方文档 (https://ai.google.dev/gemini-api/docs/image-generation?hl=zh-cn)，图像生成请求必须包含 `responseModalities: ["TEXT", "IMAGE"]` 配置

**修改位置 1** - `generate_image()` 方法 (line 304-310)：

```python
generation_config: Dict[str, Any] = {
    # 使用 ["TEXT", "IMAGE"] 以兼容所有 Gemini 图像生成模型
    "responseModalities": ["TEXT", "IMAGE"]
}
if image_config:
    generation_config["imageConfig"] = image_config
body["generationConfig"] = generation_config
```

**修改位置 2** - `image_to_image()` 方法 (line 386-392)：

```python
generation_config: Dict[str, Any] = {
    # 使用 ["TEXT", "IMAGE"] 以兼容所有 Gemini 图像生成模型
    "responseModalities": ["TEXT", "IMAGE"]
}
if image_config:
    generation_config["imageConfig"] = image_config
body["generationConfig"] = generation_config
```

### 4. 更新和增强测试 (ai-pic-backend/tests/unit/test_google_provider_image.py)

**新增断言** - 验证 `responseModalities` 字段正确设置：

```python
# 验证 responseModalities 字段已正确设置
assert "generationConfig" in dummy_client.last_request["json"]
assert "responseModalities" in dummy_client.last_request["json"]["generationConfig"]
assert dummy_client.last_request["json"]["generationConfig"]["responseModalities"] == ["TEXT", "IMAGE"]
```

添加到 `test_generate_image_success` 和 `test_image_to_image_uses_reference` 两个测试中。

### 5. 确认可用模型列表 (ai-pic-backend/app/services/providers/google_provider.py:84-106)

根据官方文档确认以下模型存在：

- `gemini-2.0-flash-exp` - 实验性图片生成模型
- `gemini-2.5-flash-image` - 快速图片生成模型（正式版）
- `gemini-3-pro-image-preview` - 专业级图片生成模型（预览版）

## Validation

### 单元测试

```bash
$ pytest tests/unit/test_google_provider_image.py -v
======================== 2 passed, 23 warnings in 0.04s ========================
🎉 所有测试通过！AI图像生成系统运行正常。
```

两个测试用例：

1. `test_generate_image_success` - 验证文生图功能和 responseModalities 配置
2. `test_image_to_image_uses_reference` - 验证图生图功能和 responseModalities 配置

### 端到端测试计划

测试步骤（使用 Chrome + DevTools）：

1. 访问 http://localhost:8089
2. 使用测试账号登录：geyunfei / Gyf@845261
3. 进入虚拟 IP 3 的图像页面：/virtual-ip/3/images
4. 选择 Google Gemini 3 Pro Image Preview 模型
5. 点击生成图像
6. 验证图像成功生成并显示

预期结果：图像生成成功，后端日志显示 `status=success`

## Next Steps

1. 等待用户进行端到端浏览器测试验证
2. 如果测试成功，考虑添加更多 Google 模型配置选项（如 aspectRatio, imageSize）
3. 监控生产环境中的 Google API 调用情况
4. 考虑添加更详细的 API 错误处理和重试逻辑

## Linked Commits

本次提交将包含以下修改：

- `ai-pic-backend/app/services/ai_service.py` - 修复 Google base_url
- `ai-pic-backend/app/services/ai_service_manager.py` - 改进错误日志
- `ai-pic-backend/app/services/providers/google_provider.py` - 添加 responseModalities 配置
- `ai-pic-backend/tests/unit/test_google_provider_image.py` - 新增测试验证
- `agent_chats/2025/12/10/2025-12-10T10-24-44Z-fix-google-image-generation.md` - 本日志文件
