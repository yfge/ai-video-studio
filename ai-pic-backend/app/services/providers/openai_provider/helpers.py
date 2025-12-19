"""
OpenAI provider helper functions.

Contains parameter handling and JSON schema utilities.
"""

from __future__ import annotations

from typing import Any, Dict


def reload_openai_params(model_id: str, temperature: float) -> Dict[str, Any]:
    """Get model-specific parameters for OpenAI API."""
    if model_id.startswith("gpt-5.1"):
        return {
            "reasoning_effort": "none",
            "temperature": 1,
        }
    if model_id.startswith("gpt-5-pro"):
        return {
            "reasoning_effort": "none",
        }

    if model_id.startswith("gpt-5"):
        return {
            "reasoning_effort": "minimal",
            "temperature": 1,
        }
    return {
        "temperature": temperature,
    }


def supports_structured_outputs(model_id: str) -> bool:
    """Check if model supports response_format.json_schema strict mode."""
    lid = (model_id or "").lower()
    prefixes = [
        "gpt-4.1",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4o-audio",
        "gpt-4o-realtime",
        "o3",
        "o1",
    ]
    return any(lid.startswith(p) for p in prefixes)


def supports_json_object(model_id: str) -> bool:
    """Check if older model supports response_format.json_object."""
    lid = (model_id or "").lower()
    prefixes = [
        "gpt-4o",
        "gpt-4.1",
        "gpt-4-turbo",
        "gpt-4-0125",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-0125",
    ]
    return any(lid.startswith(p) for p in prefixes)


def add_additional_properties_false(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively add additionalProperties: false to all objects in JSON schema.

    OpenAI structured outputs require all objects to explicitly set
    additionalProperties: false.

    Reference: https://platform.openai.com/docs/guides/structured-outputs
    """
    if not isinstance(schema, dict):
        return schema

    # Copy schema to avoid modifying original object
    result = schema.copy()

    # If it's an object type, add additionalProperties: false and fill in required
    if result.get("type") == "object":
        result["additionalProperties"] = False
        props = result.get("properties")

        # Recursively process properties
        if isinstance(props, dict):
            result["properties"] = {
                key: add_additional_properties_false(value)
                for key, value in props.items()
            }
            # OpenAI strict json_schema requires: if properties are declared,
            # required must be provided and include all property names
            result["required"] = list(result["properties"].keys())

    # Recursively process array items
    if "items" in result:
        result["items"] = add_additional_properties_false(result["items"])

    # Recursively process anyOf, oneOf, allOf
    for key in ["anyOf", "oneOf", "allOf"]:
        if key in result:
            result[key] = [
                add_additional_properties_false(item) for item in result[key]
            ]

    # Recursively process $defs (definitions)
    if "$defs" in result:
        result["$defs"] = {
            key: add_additional_properties_false(value)
            for key, value in result["$defs"].items()
        }

    return result


def is_openai_strict_schema(schema: Dict[str, Any]) -> bool:
    """
    Best-effort validation for OpenAI structured outputs strict json_schema.

    Rules enforced:
    - Every object must declare additionalProperties: false
    - If an object declares properties, it must declare required, and required
      must include exactly the same keys as properties.
    """

    def _walk(node: Any) -> bool:
        if not isinstance(node, dict):
            return True

        node_type = node.get("type")
        if node_type == "object":
            if node.get("additionalProperties") is not False:
                return False
            props = node.get("properties")
            if not isinstance(props, dict):
                return False
            required = node.get("required")
            if not isinstance(required, list):
                return False
            prop_keys = [k for k in props.keys() if isinstance(k, str)]
            if len(prop_keys) != len(props):
                return False
            if set(required) != set(prop_keys):
                return False

        if "properties" in node and isinstance(node.get("properties"), dict):
            for value in node["properties"].values():
                if not _walk(value):
                    return False

        if "items" in node:
            if not _walk(node["items"]):
                return False

        for key in ["anyOf", "oneOf", "allOf"]:
            if key in node:
                items = node.get(key)
                if not isinstance(items, list):
                    return False
                for item in items:
                    if not _walk(item):
                        return False

        if "$defs" in node:
            defs = node.get("$defs")
            if not isinstance(defs, dict):
                return False
            for value in defs.values():
                if not _walk(value):
                    return False

        return True

    return _walk(schema)
