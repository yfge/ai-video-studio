"""Deterministic typed-state output boundaries."""


def typed_delta_contract_violations(delta: dict) -> list[dict]:
    return [
        {
            "code": "canon_violation",
            "message": (
                f"{item.get('field')} 不能写入 state_transitions: "
                f"{item.get('subject_id')}"
            ),
        }
        for item in delta.get("state_transitions") or []
        if item.get("field") in {"knowledge", "location", "possessions"}
    ]
