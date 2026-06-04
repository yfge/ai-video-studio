from __future__ import annotations


def style_prompt_instruction(style: str) -> str:
    if style == "live_action":
        return (
            "真人电影 style: use believable human actors, practical production "
            "design, cinematic lighting, real camera/lens language, non-cartoon "
            "treatment; do not force cartoon styling."
        )
    if style == "2d_cartoon":
        return "Use non-real 2D cartoon characters and graphic animation styling."
    return "Use non-real 3D cartoon characters and stylized animated lighting."
