import pytest
from app.services.narrative_consistency.errors import SchemaError
from app.services.narrative_consistency.schema import freeze_schema


def test_nested_fact_in_event_effect_reports_top_level_predicate_requirement():
    schema = _schema()
    schema["event_types"][0]["effects"] = [
        {
            "op": "assert",
            "fact": {
                "subject": {"role": "actor"},
                "predicate_id": "active",
                "value": True,
            },
        }
    ]

    with pytest.raises(SchemaError, match="top-level predicate_id"):
        freeze_schema(schema)


def test_unknown_predicate_in_event_effect_reports_unknown_id():
    schema = _schema()
    schema["event_types"][0]["effects"] = [
        {
            "op": "assert",
            "subject": {"role": "actor"},
            "predicate_id": "not-in-this-story",
            "value": True,
        }
    ]

    with pytest.raises(SchemaError, match="unknown predicate"):
        freeze_schema(schema)


def _schema():
    return {
        "schema": "story_novel_consistency_schema.v1",
        "version": 1,
        "entity_types": [{"id": "actor", "label": "actor"}],
        "predicates": [
            {
                "id": "active",
                "label": "active",
                "subject_type_ids": ["actor"],
                "value_kind": "boolean",
            }
        ],
        "event_types": [
            {
                "id": "change",
                "label": "change",
                "roles": {"actor": ["actor"]},
            }
        ],
    }
