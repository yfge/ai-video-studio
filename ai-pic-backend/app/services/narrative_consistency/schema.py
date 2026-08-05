from __future__ import annotations

from typing import Any

from .contracts import ConsistencySchema
from .errors import SchemaError
from .hashing import value_hash

CONDITION_OPERATORS = frozenset(
    {"all", "any", "not", "exists", "equals", "contains", "event_before"}
)
EFFECT_OPERATORS = frozenset({"assert", "retract", "replace", "reveal", "conceal"})


def freeze_schema(value: ConsistencySchema | dict) -> dict:
    schema = ConsistencySchema.model_validate(value)
    validate_schema(schema)
    payload = schema.model_dump(exclude={"schema_hash"})
    payload["schema_hash"] = value_hash(payload)
    return payload


def validate_schema(schema: ConsistencySchema) -> None:
    types = _unique(schema.entity_types, "entity type")
    predicates = _unique(schema.predicates, "predicate")
    events = _unique(schema.event_types, "event type")
    constraints = _unique(schema.constraints, "constraint")
    perspectives = _unique(schema.perspectives, "perspective")
    for predicate in predicates.values():
        _require_refs(predicate.subject_type_ids, types, f"predicate {predicate.id}")
        if predicate.value_kind == "entity_ref":
            _require_refs(
                predicate.value_entity_type_ids,
                types,
                f"predicate {predicate.id} entity values",
            )
        elif predicate.value_entity_type_ids:
            raise SchemaError(f"predicate {predicate.id} has unused entity value types")
        if predicate.value_kind == "enum" and not predicate.enum_values:
            raise SchemaError(f"predicate {predicate.id} enum_values is empty")
        if predicate.mutability == "accumulative" and predicate.cardinality != "many":
            raise SchemaError(f"predicate {predicate.id} accumulative must be many")
    for event in events.values():
        for role, allowed in event.roles.items():
            if not role.strip() or not allowed:
                raise SchemaError(f"event {event.id} has an empty role")
            _require_refs(allowed, types, f"event {event.id} role {role}")
        for rule in event.preconditions:
            validate_condition(rule, predicates, set(event.roles), set(perspectives))
        for effect in event.effects:
            validate_effect(effect, predicates, set(event.roles), set(perspectives))
    for constraint in constraints.values():
        _validate_constraint(
            constraint.kind, constraint.expression, predicates, set(perspectives)
        )


def validate_condition(
    rule: dict[str, Any],
    predicates: dict[str, Any],
    roles: set[str],
    perspectives: set[str] | None = None,
) -> None:
    perspectives = perspectives or set()
    op = str(rule.get("op") or "")
    if op not in CONDITION_OPERATORS:
        raise SchemaError(f"unknown condition operator: {op}")
    if op in {"all", "any"}:
        args = rule.get("args")
        if not isinstance(args, list) or not args:
            raise SchemaError(f"condition {op} requires non-empty args")
        for item in args:
            validate_condition(
                _mapping(item, "condition"), predicates, roles, perspectives
            )
        return
    if op == "not":
        validate_condition(
            _mapping(rule.get("arg"), "condition"), predicates, roles, perspectives
        )
        return
    if op == "event_before":
        if not str(rule.get("event_id") or "").strip():
            raise SchemaError("event_before requires event_id")
        return
    predicate = _predicate(rule, predicates)
    if _field(predicate, "persistence") != "causal":
        raise SchemaError(
            f"observational predicate {_field(predicate, 'id')} cannot be a dependency"
        )
    _validate_selector(rule.get("subject"), roles, "condition subject")
    if rule.get("scope", "objective") == "perspective":
        if rule.get("perspective_id") not in perspectives:
            raise SchemaError(f"condition {op} has unknown perspective")
    elif rule.get("perspective_id"):
        raise SchemaError(f"condition {op} binds perspective as objective")
    if op in {"equals", "contains"} and "value" not in rule:
        raise SchemaError(f"condition {op} requires value")


def validate_effect(
    effect: dict[str, Any],
    predicates: dict[str, Any],
    roles: set[str],
    perspectives: set[str] | None = None,
) -> None:
    perspectives = perspectives or set()
    op = str(effect.get("op") or "")
    if op not in EFFECT_OPERATORS:
        raise SchemaError(f"unknown effect operator: {op}")
    predicate = _predicate(effect, predicates)
    if _field(predicate, "persistence") != "causal":
        raise SchemaError(
            f"event effects cannot persist observation {_field(predicate, 'id')}"
        )
    _validate_selector(effect.get("subject"), roles, "effect subject")
    if op != "retract" and "value" not in effect:
        raise SchemaError(f"effect {op} requires value")
    if op in {"reveal", "conceal"} and not effect.get("perspective_id"):
        raise SchemaError(f"effect {op} requires perspective_id")
    if (
        effect.get("perspective_id")
        and effect.get("perspective_id") not in perspectives
    ):
        raise SchemaError(f"effect {op} has unknown perspective")
    if effect.get("scope") == "perspective" and (
        not effect.get("perspective_id")
        or effect.get("perspective_state")
        not in {"known", "believed", "suspected", "hidden"}
    ):
        raise SchemaError(f"effect {op} has invalid perspective metadata")
    if (
        effect.get("scope", "objective") == "objective"
        and (effect.get("perspective_id") or effect.get("perspective_state"))
        and op not in {"reveal", "conceal"}
    ):
        raise SchemaError(f"effect {op} binds perspective metadata as objective")


def _validate_constraint(kind, expression, predicates, perspectives) -> None:
    expression = _mapping(expression, "constraint expression")
    if kind in {"invariant", "mutual_exclusion"}:
        rules = (
            [expression] if kind == "invariant" else expression.get("conditions") or []
        )
        if not rules:
            raise SchemaError(f"constraint {kind} requires conditions")
        for rule in rules:
            validate_condition(
                _mapping(rule, "condition"), predicates, set(), perspectives
            )
        return
    if kind == "unique":
        _predicate(expression, predicates)
        return
    for field in ("before_event_id", "after_event_id"):
        if not str(expression.get(field) or "").strip():
            raise SchemaError(f"constraint {kind} requires {field}")


def _predicate(rule, predicates):
    predicate_id = str(rule.get("predicate_id") or "")
    predicate = predicates.get(predicate_id)
    if not predicate:
        raise SchemaError(f"unknown predicate: {predicate_id}")
    return predicate


def _validate_selector(value, roles: set[str], label: str) -> None:
    if isinstance(value, str) and value.strip():
        return
    if isinstance(value, dict) and set(value) == {"role"}:
        if value["role"] in roles:
            return
        raise SchemaError(f"{label} uses unknown role: {value['role']}")
    raise SchemaError(f"{label} must be entity id or role selector")


def _unique(rows, label: str):
    result = {item.id: item for item in rows}
    if len(result) != len(rows) or any(not key.strip() for key in result):
        raise SchemaError(f"duplicate or blank {label} id")
    return result


def _require_refs(values, known, label: str) -> None:
    unknown = sorted(set(values) - set(known))
    if unknown:
        raise SchemaError(f"{label} references unknown ids: {unknown}")


def _mapping(value, label: str) -> dict:
    if not isinstance(value, dict):
        raise SchemaError(f"{label} must be an object")
    return value


def _field(value, name: str):
    return value[name] if isinstance(value, dict) else getattr(value, name)
