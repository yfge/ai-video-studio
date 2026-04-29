from __future__ import annotations

import json
from typing import Any, Dict, Optional

QUALITY_GATE_ERROR_CODE = "quality_gate_failed"
MAX_QUALITY_GATE_REPAIRS = 2


class NarrativeQualityGateError(RuntimeError):
    def __init__(self, kind: str, quality_gate: Dict[str, Any]) -> None:
        self.kind = kind
        self.quality_gate = quality_gate
        issues = quality_gate.get("blocking_issues") or []
        summary = "; ".join(str(i.get("message")) for i in issues[:3])
        super().__init__(summary or f"{kind} quality gate failed")


def make_quality_check(
    check_id: str,
    passed: bool,
    message: str,
    *,
    severity: str = "error",
    score: float | None = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "id": check_id,
        "passed": bool(passed),
        "severity": severity,
        "score": 1.0 if score is None and passed else (0.0 if score is None else score),
        "message": message,
        "details": details or {},
    }


def build_quality_gate_report(
    *,
    kind: str,
    checks: list[Dict[str, Any]],
    repair_attempts: Optional[list[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    blocking = [
        c
        for c in checks
        if not c.get("passed") and c.get("severity") in {"error", "blocker"}
    ]
    warnings = [
        c
        for c in checks
        if not c.get("passed") and c.get("severity") not in {"error", "blocker"}
    ]
    total_weight = len(checks) or 1
    score = round(
        10.0 * sum(float(c.get("score", 0.0)) for c in checks) / total_weight,
        2,
    )
    return {
        "kind": kind,
        "passed": not blocking,
        "score": score,
        "blocking_issues": blocking,
        "warnings": warnings,
        "checks": checks,
        "repair_attempts": repair_attempts or [],
    }


def quality_gate_attempt_snapshot(quality_gate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "passed": quality_gate.get("passed"),
        "score": quality_gate.get("score"),
        "blocking_issues": quality_gate.get("blocking_issues") or [],
        "warnings": quality_gate.get("warnings") or [],
    }


def attach_quality_gate_failure_to_task(
    task: Any, quality_gate: Dict[str, Any]
) -> None:
    from app.services.task_agent_run.utils import deep_merge_dict, loads_task_parameters

    params = loads_task_parameters(getattr(task, "parameters", None))
    task.parameters = json.dumps(
        deep_merge_dict(
            params,
            {
                "agent_run": {
                    "quality_gate": quality_gate,
                    "error": {
                        "code": QUALITY_GATE_ERROR_CODE,
                        "message": "Strict narrative quality gate failed",
                    },
                }
            },
        ),
        ensure_ascii=False,
    )
