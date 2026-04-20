#!/usr/bin/env python3
"""Shared log-query helpers for harness observability."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scripts.harness._common import find_jsonl_log


def load_log_records(log_path: Path | None = None) -> list[dict[str, Any]]:
    path = log_path or find_jsonl_log()
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(raw_line))
        except json.JSONDecodeError:
            continue
    return records


def filter_log_records(
    records: list[dict[str, Any]],
    *,
    run_id: str | None = None,
    task_id: str | None = None,
    route: str | None = None,
    level: str | None = None,
) -> list[dict[str, Any]]:
    filtered = []
    for record in records:
        if run_id and str(record.get("run_id")) != run_id:
            continue
        if task_id and str(record.get("task_id")) != task_id:
            continue
        if route and str(record.get("route")) != route:
            continue
        if level and str(record.get("level")).upper() != level.upper():
            continue
        filtered.append(record)
    return filtered


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _percentile(values: list[int], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * ratio))))
    return float(ordered[index])


def summarize_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [_safe_int(record.get("latency_ms")) for record in records]
    latency_values = [value for value in latencies if value is not None]
    status_counts = Counter(str(record.get("status")) for record in records if record.get("status"))
    level_counts = Counter(str(record.get("level")) for record in records if record.get("level"))
    route_latency: dict[str, list[int]] = defaultdict(list)
    error_samples: list[dict[str, Any]] = []

    for record in records:
        latency = _safe_int(record.get("latency_ms"))
        route = str(record.get("route") or "unknown")
        if latency is not None:
            route_latency[route].append(latency)
        if str(record.get("level", "")).upper() in {"WARNING", "ERROR", "CRITICAL"}:
            error_samples.append(
                {
                    "timestamp": record.get("timestamp"),
                    "level": record.get("level"),
                    "route": record.get("route"),
                    "message": record.get("message"),
                    "status": record.get("status"),
                }
            )

    route_breakdown = []
    for route, values in sorted(route_latency.items()):
        route_breakdown.append(
            {
                "route": route,
                "count": len(values),
                "avg_latency_ms": round(sum(values) / len(values), 2),
                "p95_latency_ms": _percentile(values, 0.95),
            }
        )

    return {
        "record_count": len(records),
        "unique_request_ids": len({record.get("request_id") for record in records if record.get("request_id")}),
        "status_counts": dict(sorted(status_counts.items())),
        "level_counts": dict(sorted(level_counts.items())),
        "latency_ms": {
            "avg": round(sum(latency_values) / len(latency_values), 2) if latency_values else 0.0,
            "p95": _percentile(latency_values, 0.95),
            "max": max(latency_values) if latency_values else 0,
        },
        "route_breakdown": route_breakdown,
        "error_samples": error_samples[:20],
    }
