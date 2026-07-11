HAILUO_768P_MODELS = {
    "MiniMax-Hailuo-2.3",
    "MiniMax-Hailuo-2.3-Fast",
    "MiniMax-Hailuo-02",
}


def normalize_minimax_video_resolution(model: str, resolution: str) -> str:
    value = str(resolution or "").strip() or "768P"
    if model in HAILUO_768P_MODELS and value.lower() in {"720p", "1280x720"}:
        return "768P"
    return value
