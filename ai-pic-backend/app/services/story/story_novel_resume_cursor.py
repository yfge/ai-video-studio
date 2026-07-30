"""Advance the persisted resume cursor after a chapter becomes ready."""


def advance_resume_cursor(revision, plan_rows) -> None:
    ledger = dict(revision.continuity_ledger or {})
    if ledger.get("stale_from_position") is None:
        return
    entries = ledger.get("chapters") or {}
    pending = [
        int(row["position"])
        for row in plan_rows
        if (entries.get(str(row["position"])) or {}).get("status") != "ready"
    ]
    if pending:
        ledger.update(state_status="stale", stale_from_position=min(pending))
    else:
        ledger["state_status"] = "ready"
        ledger.pop("stale_from_position", None)
    revision.continuity_ledger = ledger
