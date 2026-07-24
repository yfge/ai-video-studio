from fastapi import HTTPException


def ensure_direct_episode_generation_allowed(story) -> None:
    if getattr(story, "workflow_mode", "direct") == "novel_adaptation_v1":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "NOVEL_APPROVAL_REQUIRED",
                "message": (
                    "小说工作流禁止从 Story/StorySeed 直接生成剧集；"
                    "请按“小说审批 → 改编计划审批 → 创建剧集”执行"
                ),
            },
        )


def ensure_direct_episode_regeneration_allowed(story) -> None:
    if getattr(story, "workflow_mode", "direct") == "novel_adaptation_v1":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "NOVEL_EPISODE_REGENERATION_REQUIRES_PLAN",
                "message": (
                    "小说工作流禁止用旧自由生成链路重生成剧集；"
                    "请从当前 canonical 小说创建并审批新的改编计划"
                ),
            },
        )
