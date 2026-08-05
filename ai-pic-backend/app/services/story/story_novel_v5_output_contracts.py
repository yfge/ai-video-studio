"""Provider-facing JSON Schemas for V5 structured planning calls."""

from __future__ import annotations

from functools import lru_cache

from app.services.narrative_consistency.contracts import (
    CausalEventGraph,
    ConsistencySchema,
    FactGraph,
)
from pydantic import BaseModel, ConfigDict


class FoundationCompilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consistency_schema: ConsistencySchema
    initial_fact_graph: FactGraph


class CausalBatchCompilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    causal_event_graph: CausalEventGraph


class FullCompilePayload(FoundationCompilePayload):
    causal_event_graph: CausalEventGraph


@lru_cache(maxsize=1)
def foundation_output_schema() -> dict:
    return _tighten_contract(FoundationCompilePayload.model_json_schema())


@lru_cache(maxsize=1)
def causal_batch_output_schema() -> dict:
    return _tighten_contract(CausalBatchCompilePayload.model_json_schema())


@lru_cache(maxsize=1)
def full_compile_output_schema() -> dict:
    return _tighten_contract(FullCompilePayload.model_json_schema())


def _tighten_contract(value: dict) -> dict:
    _require_schema_literals(value)
    _require_rule_shapes(value)
    return value


def _require_schema_literals(value: dict) -> dict:
    """Keep shadowed Pydantic ``schema`` fields required across v2 releases."""
    for name in ("ConsistencySchema", "FactGraph", "CausalEventGraph"):
        definition = (value.get("$defs") or {}).get(name)
        if not isinstance(definition, dict):
            continue
        required = list(definition.get("required") or [])
        if "schema" not in required:
            definition["required"] = ["schema", *required]
    return value


def _require_rule_shapes(value: dict) -> None:
    definitions = value.setdefault("$defs", {})
    definitions["EntityOrRoleSelector"] = {
        "oneOf": [
            {"type": "string", "minLength": 1},
            {
                "type": "object",
                "properties": {"role": {"type": "string", "minLength": 1}},
                "required": ["role"],
                "additionalProperties": False,
            },
        ]
    }
    definitions["ConditionRule"] = _condition_rule_schema()
    definitions["EffectRule"] = _effect_rule_schema()
    for name in ("EventType", "CausalEvent"):
        properties = (definitions.get(name) or {}).get("properties") or {}
        if "preconditions" in properties:
            properties["preconditions"]["items"] = {"$ref": "#/$defs/ConditionRule"}
        if "effects" in properties:
            properties["effects"]["items"] = {"$ref": "#/$defs/EffectRule"}


def _condition_rule_schema() -> dict:
    selector = {"$ref": "#/$defs/EntityOrRoleSelector"}
    perspective = {
        "scope": {"enum": ["objective", "perspective"]},
        "perspective_id": {"type": "string", "minLength": 1},
    }
    predicate_leaf = {
        "properties": {
            "op": {"const": "exists"},
            "predicate_id": {"type": "string", "minLength": 1},
            "subject": selector,
            **perspective,
        },
        "required": ["op", "predicate_id", "subject"],
        "additionalProperties": False,
    }
    value_leaf = {
        "properties": {
            "op": {"enum": ["equals", "contains"]},
            "predicate_id": {"type": "string", "minLength": 1},
            "subject": selector,
            "value": {},
            **perspective,
        },
        "required": ["op", "predicate_id", "subject", "value"],
        "additionalProperties": False,
    }
    return {
        "oneOf": [
            {
                "properties": {
                    "op": {"enum": ["all", "any"]},
                    "args": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/$defs/ConditionRule"},
                    },
                },
                "required": ["op", "args"],
                "additionalProperties": False,
            },
            {
                "properties": {
                    "op": {"const": "not"},
                    "arg": {"$ref": "#/$defs/ConditionRule"},
                },
                "required": ["op", "arg"],
                "additionalProperties": False,
            },
            {
                "properties": {
                    "op": {"const": "event_before"},
                    "event_id": {"type": "string", "minLength": 1},
                },
                "required": ["op", "event_id"],
                "additionalProperties": False,
            },
            predicate_leaf,
            value_leaf,
        ]
    }


def _effect_rule_schema() -> dict:
    properties = {
        "predicate_id": {"type": "string", "minLength": 1},
        "subject": {"$ref": "#/$defs/EntityOrRoleSelector"},
        "scope": {"enum": ["objective", "perspective"]},
        "perspective_id": {"type": "string", "minLength": 1},
        "perspective_state": {"enum": ["known", "believed", "suspected", "hidden"]},
    }
    return {
        "oneOf": [
            {
                "properties": {"op": {"const": "retract"}, **properties},
                "required": ["op", "predicate_id", "subject"],
                "additionalProperties": False,
            },
            {
                "properties": {
                    "op": {"enum": ["assert", "replace"]},
                    **properties,
                    "value": {},
                },
                "required": ["op", "predicate_id", "subject", "value"],
                "additionalProperties": False,
            },
            {
                "properties": {
                    "op": {"enum": ["reveal", "conceal"]},
                    **properties,
                    "value": {},
                },
                "required": [
                    "op",
                    "predicate_id",
                    "subject",
                    "value",
                    "perspective_id",
                ],
                "additionalProperties": False,
            },
        ]
    }
