---
id: 2025-12-10T11-01-15Z-fix-openai-json-schema
date: 2025-12-10T11:01:15Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, openai, json-schema, story-generation, bug-fix]
related_paths:
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-backend/tests/unit/test_openai_schema_fix.py
summary: "修复 OpenAI structured outputs JSON schema 错误：递归添加 additionalProperties: false"
---

## User Prompt

用户在故事生成功能中遇到OpenAI API 400错误：
```
OpenAI stream status 400 body={
  "error": {
    "message": "Invalid schema for response_format 'story_outline': In context=(), 'additionalProperties' is required to be supplied and to be false.",
    "type": "invalid_request_error",
    "param": "response_format",
    "code": null
  }
}
```

Request body 显示：
```json
{
  "title": "大杀四方",
  "genre": "sci-fi",
  "model": "",  // 前端未传入模型
  ...
}
```

## Goals

1. 修复 OpenAI structured outputs 的 JSON schema 要求
2. 确保所有对象类型都包含 `additionalProperties: false`
3. 添加测试验证 schema 修复逻辑
4. 保持对现有功能的兼容性

## Changes

### 1. 添加 _add_additional_properties_false 函数 (ai-pic-backend/app/services/providers/openai_provider.py:68-108)

**新增辅助函数**：
```python
def _add_additional_properties_false(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归地为 JSON schema 中的所有对象添加 additionalProperties: false。
    OpenAI structured outputs 要求所有对象都必须显式设置 additionalProperties: false。

    参考：https://platform.openai.com/docs/guides/structured-outputs
    """
    if not isinstance(schema, dict):
        return schema

    # 复制schema避免修改原对象
    result = schema.copy()

    # 如果是对象类型，添加 additionalProperties: false
    if result.get("type") == "object":
        result["additionalProperties"] = False

        # 递归处理 properties
        if "properties" in result:
            result["properties"] = {
                key: _add_additional_properties_false(value)
                for key, value in result["properties"].items()
            }

    # 递归处理数组的 items
    if "items" in result:
        result["items"] = _add_additional_properties_false(result["items"])

    # 递归处理 anyOf, oneOf, allOf
    for key in ["anyOf", "oneOf", "allOf"]:
        if key in result:
            result[key] = [_add_additional_properties_false(item) for item in result[key]]

    # 递归处理 $defs (definitions)
    if "$defs" in result:
        result["$defs"] = {
            key: _add_additional_properties_false(value)
            for key, value in result["$defs"].items()
        }

    return result
```

**功能**：
- 递归遍历整个 JSON schema
- 为所有 `type: "object"` 的节点添加 `"additionalProperties": false`
- 处理嵌套对象、数组items、anyOf/oneOf/allOf、$defs等复杂结构
- 不修改原对象，返回新的 schema 副本

**原因**：
- OpenAI structured outputs (GPT-4o+) 要求所有对象**必须**显式设置 `"additionalProperties": false`
- Pydantic 生成的 JSON schema 默认不包含此字段
- 缺少此字段会导致 400 错误

### 2. 在 generate_text 中应用修复 (line 324-326)

**修改前**：
```python
if _supports_structured_outputs(model):
    payload["response_format"] = {
        "type": "json_schema",
        "json_schema": {
            "name": json_schema.get("name", "response"),
            "schema": json_schema.get("schema", json_schema),
            "strict": True,
        },
    }
```

**修改后**：
```python
if _supports_structured_outputs(model):
    # 获取原始 schema 并添加 additionalProperties: false
    raw_schema = json_schema.get("schema", json_schema)
    fixed_schema = _add_additional_properties_false(raw_schema)

    payload["response_format"] = {
        "type": "json_schema",
        "json_schema": {
            "name": json_schema.get("name", "response"),
            "schema": fixed_schema,
            "strict": True,
        },
    }
```

### 3. 新增测试 (ai-pic-backend/tests/unit/test_openai_schema_fix.py)

创建了7个测试用例覆盖各种场景：

1. ✅ `test_add_additional_properties_to_simple_object` - 简单对象
2. ✅ `test_add_additional_properties_to_nested_objects` - 嵌套对象
3. ✅ `test_add_additional_properties_to_array_items` - 数组items
4. ✅ `test_add_additional_properties_with_defs` - $defs 定义
5. ✅ `test_add_additional_properties_with_anyof` - anyOf 联合类型
6. ✅ `test_preserves_existing_additional_properties` - 覆盖已存在的值
7. ✅ `test_does_not_modify_non_objects` - 不修改非对象类型

## Validation

### 单元测试
```bash
$ pytest tests/unit/test_openai_schema_fix.py -v
======================== 7 passed, 25 warnings in 0.04s ========================
🎉 所有测试通过！
```

### 修复前后对比

**修复前的 Schema**（Pydantic 生成）：
```json
{
  "type": "object",
  "properties": {
    "premise": {"type": "string"},
    "character_relationships": {
      "type": "object",
      "properties": {
        "data": {"type": "string"}
      }
      // ❌ 缺少 additionalProperties
    }
  }
  // ❌ 缺少 additionalProperties
}
```

**修复后的 Schema**（自动添加）：
```json
{
  "type": "object",
  "additionalProperties": false,  // ✅ 已添加
  "properties": {
    "premise": {"type": "string"},
    "character_relationships": {
      "type": "object",
      "additionalProperties": false,  // ✅ 已添加
      "properties": {
        "data": {"type": "string"}
      }
    }
  }
}
```

### 端到端测试计划
测试步骤：
1. 访问故事生成页面（/stories/new）
2. 填写故事信息（标题、类型、角色等）
3. 选择 OpenAI GPT-4o 或 GPT-4o-mini 模型
4. 点击生成故事概要

预期结果：
- OpenAI API 调用成功
- 返回符合 StoryOutlineModel 格式的 JSON数据
- 后端日志显示 `status=success`

## Next Steps

1. ✅ 解决了 OpenAI JSON schema 问题
2. ⚠️ 需要处理前端未传入模型参数的问题（`"model": ""`）
3. ⚠️ 需要修复其他 provider 的模型配置问题：
   - Volcengine: `doubao-lite-4k` 模型不存在
   - Google: `gemini-3-pro-preview` 文本模型 404
4. 监控生产环境中的故事生成功能

## Linked Commits

本次提交将包含以下修改：
- `ai-pic-backend/app/services/providers/openai_provider.py` - 添加并应用 _add_additional_properties_false
- `ai-pic-backend/tests/unit/test_openai_schema_fix.py` - 新增测试验证
- `agent_chats/2025/12/10/2025-12-10T11-01-15Z-fix-openai-json-schema.md` - 本日志文件

## References

- [OpenAI Structured Outputs Guide](https://platform.openai.com/docs/guides/structured-outputs)
- [JSON Schema additionalProperties](https://json-schema.org/understanding-json-schema/reference/object.html#additional-properties)
