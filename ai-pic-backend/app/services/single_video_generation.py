from __future__ import annotations

from app.schemas.generation_requests import ScriptGenerationRequest


def build_single_video_script_request(
    *,
    episode_id: int,
    prompt: str,
    duration_seconds: int,
    aspect_ratio: str,
    style: str | None = None,
) -> ScriptGenerationRequest:
    constraints = [
        "## 系统生产约束（优先级最高）",
        f"- 成片总时长：{duration_seconds} 秒。",
        f"- 标题、logline、概要、场景时长和正文必须统一按 {duration_seconds} 秒成片。",
        "- 该规格来自用户显式设置或对原始目标的结构化解析。",
        "- 其他数字只有在明确属于剧情时才能作为戏内数字。",
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
        target_chars_per_episode=max(600, min(2500, round(duration_seconds * 5))),
        additional_requirements=requirements,
        style_preferences=[style] if style else None,
    )
