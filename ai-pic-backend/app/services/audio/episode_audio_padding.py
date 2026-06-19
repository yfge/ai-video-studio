from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def pad_to_episode_target_duration(
    episode: Any,
    timeline_beats: list[dict[str, Any]],
    duration_ms_total: int,
) -> tuple[list[dict[str, Any]], int, int]:
    target_ms = _episode_target_duration_ms(episode)
    if target_ms is None or duration_ms_total >= target_ms:
        return timeline_beats, duration_ms_total, 0
    padding_ms = target_ms - duration_ms_total
    if padding_ms <= 0:
        return timeline_beats, duration_ms_total, 0

    padded = list(timeline_beats)
    last = padded[-1] if padded else {}
    cursor = duration_ms_total
    remaining = padding_ms
    index = 1
    while remaining > 0:
        segment_ms = min(8000, remaining)
        padded.append(
            _tail_padding_beat(
                last=last,
                index=index,
                start_ms=cursor,
                end_ms=cursor + segment_ms,
            )
        )
        cursor += segment_ms
        remaining -= segment_ms
        index += 1

    logger.info(
        "Episode timeline padded to target duration",
        extra={
            "episode_id": getattr(episode, "id", None),
            "target_duration_ms": target_ms,
            "original_duration_ms": duration_ms_total,
            "padding_ms": padding_ms,
            "padding_beats": index - 1,
        },
    )
    return padded, cursor, padding_ms


def _tail_padding_beat(
    *,
    last: dict[str, Any],
    index: int,
    start_ms: int,
    end_ms: int,
) -> dict[str, Any]:
    return {
        "scene_id": last.get("scene_id"),
        "scene_number": last.get("scene_number"),
        "beat_id": f"tail_pad_{index}",
        "beat_type": "action",
        "speaker_name": None,
        "text": _tail_padding_action(index),
        "start_ms": start_ms,
        "end_ms": end_ms,
        "padding": True,
        "padding_reason": "extend_to_episode_target_duration",
    }


def _episode_target_duration_ms(episode: Any) -> int | None:
    value = getattr(episode, "duration_minutes", None)
    try:
        minutes = float(value)
    except (TypeError, ValueError):
        return None
    if minutes <= 0:
        return None
    return int(round(minutes * 60 * 1000))


def _tail_padding_action(index: int) -> str:
    actions = (
        "AP手机倒计时继续跳动，投影原始文件删除进度条缓慢推进。",
        "小陈连续敲键盘维持日志锁定，蓝色锁图标被红光压住。",
        "张总把签字纪要压在桌上，会议室只剩键盘声和倒计时。",
        "AP盯着屏幕不眨眼，备份硬盘指示灯一下一下闪烁。",
    )
    return actions[(index - 1) % len(actions)]
