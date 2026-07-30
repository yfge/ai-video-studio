"""Persist a planning failure before stopping prose generation."""

from fastapi import HTTPException


def fail_plan(service, revision, phase: str, error: str | None) -> None:
    revision.generation_plan = {
        **dict(revision.generation_plan or {}),
        "status": "failed",
        "phase": phase,
        "error": error or "invalid generation plan",
    }
    service.db.commit()
    detail = "Canon 编译无效" if phase == "canon" else "章节规划无效"
    raise HTTPException(status_code=500, detail=f"{detail}，正文尚未生成")
