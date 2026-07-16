from __future__ import annotations

from app.schemas.generation_requests import ScriptGenerationRequest


def build_single_video_script_request(
    *,
    episode_id: int,
    prompt: str,
    duration_minutes: int,
    aspect_ratio: str,
    style: str | None = None,
) -> ScriptGenerationRequest:
    constraints = [
        "## 系统生产约束（优先级最高）",
        f"- 成片总时长：{duration_minutes} 分钟。",
        "- 用户创意描述中的其他成片时长不生效，以系统生产时长为准。",
        "- 内容形态：独立单条视频，不得扩展为多集。",
        f"- 目标画幅：{aspect_ratio}。",
    ]
    if style:
        constraints.append(f"- 视觉与叙事风格：{style}。")
    requirements = "\n".join(
        [
            *constraints,
            "## 用户创意描述",
            prompt.strip(),
        ]
    )
    return ScriptGenerationRequest(
        episode_id=episode_id,
        generation_mode="production",
        auto_timeline_pipeline=True,
        target_chars_per_episode=max(600, min(2500, duration_minutes * 300)),
        additional_requirements=requirements,
        style_preferences=[style] if style else None,
    )
