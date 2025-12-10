"""测试 OpenAI provider 的 JSON schema additionalProperties 修复"""

import pytest
from app.services.providers.openai_provider import _add_additional_properties_false


def test_add_additional_properties_to_simple_object():
    """测试为简单对象添加 additionalProperties: false"""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }
    }

    result = _add_additional_properties_false(schema)

    assert result["additionalProperties"] is False
    assert "properties" in result
    assert result["properties"]["name"] == {"type": "string"}


def test_add_additional_properties_to_nested_objects():
    """测试为嵌套对象递归添加 additionalProperties: false"""
    schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "address": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"}
                        }
                    }
                }
            }
        }
    }

    result = _add_additional_properties_false(schema)

    # 顶层对象
    assert result["additionalProperties"] is False

    # 嵌套的 user 对象
    user_schema = result["properties"]["user"]
    assert user_schema["additionalProperties"] is False

    # 更深层的 address 对象
    address_schema = user_schema["properties"]["address"]
    assert address_schema["additionalProperties"] is False


def test_add_additional_properties_to_array_items():
    """测试为数组items中的对象添加 additionalProperties: false"""
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"}
                    }
                }
            }
        }
    }

    result = _add_additional_properties_false(schema)

    # 顶层对象
    assert result["additionalProperties"] is False

    # 数组items中的对象
    item_schema = result["properties"]["items"]["items"]
    assert item_schema["additionalProperties"] is False


def test_add_additional_properties_with_defs():
    """测试处理 $defs (definitions) 中的对象"""
    schema = {
        "type": "object",
        "properties": {
            "data": {"$ref": "#/$defs/DataObject"}
        },
        "$defs": {
            "DataObject": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"}
                }
            }
        }
    }

    result = _add_additional_properties_false(schema)

    # 顶层对象
    assert result["additionalProperties"] is False

    # $defs 中的对象
    data_object = result["$defs"]["DataObject"]
    assert data_object["additionalProperties"] is False


def test_add_additional_properties_with_anyof():
    """测试处理 anyOf 中的对象"""
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "anyOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "properties": {
                            "complex": {"type": "boolean"}
                        }
                    }
                ]
            }
        }
    }

    result = _add_additional_properties_false(schema)

    # 顶层对象
    assert result["additionalProperties"] is False

    # anyOf 中的对象
    any_of_items = result["properties"]["value"]["anyOf"]
    assert any_of_items[0] == {"type": "string"}  # 非对象类型不变
    assert any_of_items[1]["additionalProperties"] is False  # 对象类型添加了 additionalProperties


def test_preserves_existing_additional_properties():
    """测试保留已存在的 additionalProperties 设置"""
    schema = {
        "type": "object",
        "additionalProperties": True,  # 已存在，但会被覆盖为 False
        "properties": {
            "name": {"type": "string"}
        }
    }

    result = _add_additional_properties_false(schema)

    # OpenAI 要求必须为 False，所以覆盖原值
    assert result["additionalProperties"] is False


def test_does_not_modify_non_objects():
    """测试不修改非对象类型"""
    schema = {"type": "string"}

    result = _add_additional_properties_false(schema)

    assert result == {"type": "string"}
    assert "additionalProperties" not in result
