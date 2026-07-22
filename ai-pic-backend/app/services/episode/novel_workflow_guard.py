from fastapi import HTTPException


def ensure_direct_episode_generation_allowed(story) -> None:
    if getattr(story, "workflow_mode", "direct") == "novel_adaptation_v1":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "NOVEL_APPROVAL_REQUIRED",
                "message": "请先审批小说和分集改编计划，再创建剧集",
            },
        )
