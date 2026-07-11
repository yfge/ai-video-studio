from __future__ import annotations

from typing import Any

LINEAGE_KEY = "canvas_candidate_lineage"


def record_canvas_candidate_lineage(
    frame: dict[str, Any],
    urls: list[str],
    context: dict[str, Any] | None,
    *,
    task_id: int,
) -> None:
    if not isinstance(context, dict):
        return
    parent_id = context.get("parent_candidate_id")
    run_id = context.get("run_id")
    node_id = context.get("node_id")
    if not isinstance(parent_id, int) or not run_id or not node_id:
        return
    entries = [item for item in frame.get(LINEAGE_KEY, []) if isinstance(item, dict)]
    known = {item.get("url") for item in entries}
    instruction = context.get("instruction")
    for url in urls:
        if not isinstance(url, str) or not url.strip() or url in known:
            continue
        entries.append(
            {
                "url": url,
                "run_id": str(run_id),
                "node_id": str(node_id),
                "parent_candidate_id": parent_id,
                "branch_task_id": task_id,
                "branch_instruction": (
                    instruction.strip()
                    if isinstance(instruction, str) and instruction.strip()
                    else None
                ),
            }
        )
        known.add(url)
    frame[LINEAGE_KEY] = entries
