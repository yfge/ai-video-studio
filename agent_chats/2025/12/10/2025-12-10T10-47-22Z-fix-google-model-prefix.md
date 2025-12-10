---
id: 2025-12-10T10-47-22Z-fix-google-model-prefix
date: 2025-12-10T10:47:22Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, google, image-generation, bug-fix]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-backend/tests/unit/test_google_provider_image.py
summary: "修复 Google provider 前缀问题：去除模型名称中的 'google:' 前缀以匹配 API 要求"
---

## User Prompt

用户在测试时遇到新的错误：
```
ERROR: google 错误: Client error '404 Not Found' for url 'https://generativelanguage.googleapis.com/v1beta/models/google:gemini-3-pro-image-preview:generateContent'
```

请求 body 显示：
```
"model": "google:gemini-3-pro-image-preview"
```

## Goals

1. 修复模型名称中包含 provider 前缀导致的 404 错误
2. 确保 Google API 调用使用正确的模型名称格式
3. 添加测试验证 provider 前缀被正确清理

## Changes

### 1. 添加模型 ID 清理方法 (ai-pic-backend/app/services/providers/google_provider.py:235-242)

**新增方法**：
```python
def _clean_model_id(self, model: Optional[str]) -> Optional[str]:
    """清理模型 ID，去掉可能的 provider 前缀（如 'google:'）"""
    if not model:
        return None
    # 去掉 provider 前缀（例如 "google:gemini-3-pro-image-preview" -> "gemini-3-pro-image-preview"）
    if ":" in model:
        return model.split(":", 1)[1]
    return model
```

**原因**：
- 前端/API 传入的模型名称格式为 `provider:model_id`（如 `google:gemini-3-pro-image-preview`）
- Google API 只接受纯模型 ID（如 `gemini-3-pro-image-preview`）
- 需要在调用 API 前清理掉 provider 前缀

### 2. 在 generate_image() 中应用清理逻辑 (line 298)

**修改前**：
```python
model_id = model or "gemini-2.5-flash-image"
```

**修改后**：
```python
# 清理模型 ID，去掉可能的 provider 前缀
model_id = self._clean_model_id(model) or "gemini-2.5-flash-image"
```

### 3. 在 image_to_image() 中应用清理逻辑 (line 375)

**修改前**：
```python
model_id = model or "gemini-2.5-flash-image"
```

**修改后**：
```python
# 清理模型 ID，去掉可能的 provider 前缀
model_id = self._clean_model_id(model) or "gemini-2.5-flash-image"
```

### 4. 新增测试验证前缀清理 (ai-pic-backend/tests/unit/test_google_provider_image.py:70-101)

```python
@pytest.mark.asyncio
async def test_generate_image_strips_provider_prefix(monkeypatch):
    """测试模型名称中的 provider 前缀被正确清理"""
    provider = GoogleProvider(ProviderConfig(name="google", api_key="test-key"))
    # ... 设置 mock client ...

    # 使用带有 provider 前缀的模型名称
    resp = await provider.generate_image(prompt="test image", model="google:gemini-3-pro-image-preview")

    assert resp.success is True
    # 验证 URL 中的模型名称不包含 provider 前缀
    assert "google:gemini-3-pro-image-preview" not in dummy_client.last_request["url"]
    assert "gemini-3-pro-image-preview" in dummy_client.last_request["url"]
```

## Validation

### 单元测试
```bash
$ pytest tests/unit/test_google_provider_image.py -v
======================== 3 passed, 23 warnings in 0.04s ========================
🎉 所有测试通过！AI图像生成系统运行正常。
```

三个测试用例：
1. `test_generate_image_success` - 验证基本文生图功能
2. `test_generate_image_strips_provider_prefix` - ✨ 新增：验证 provider 前缀清理
3. `test_image_to_image_uses_reference` - 验证图生图功能

### 端到端测试计划
测试步骤：
1. 在浏览器中访问故事结构环境图像生成页面
2. 选择 Google Gemini 3 Pro Image Preview 模型（model="google:gemini-3-pro-image-preview"）
3. 输入提示词（如 "幼儿园"）
4. 点击生成

预期结果：
- 后端日志显示正确的 API URL（不包含 "google:" 前缀）
- 图像成功生成

### 修复前后对比

**修复前**：
```
URL: https://generativelanguage.googleapis.com/v1beta/models/google:gemini-3-pro-image-preview:generateContent
错误: 404 Not Found
```

**修复后**：
```
URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent
状态: 成功生成图像
```

## Next Steps

1. 等待用户进行端到端浏览器测试验证
2. 考虑在其他 provider 中也添加类似的前缀清理逻辑（如果需要）
3. 监控生产环境中的 Google API 调用情况

## Linked Commits

本次提交将包含以下修改：
- `ai-pic-backend/app/services/providers/google_provider.py` - 添加 _clean_model_id 方法并应用
- `ai-pic-backend/tests/unit/test_google_provider_image.py` - 新增前缀清理测试
- `agent_chats/2025/12/10/2025-12-10T10-47-22Z-fix-google-model-prefix.md` - 本日志文件
