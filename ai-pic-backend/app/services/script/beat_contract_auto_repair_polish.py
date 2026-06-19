from __future__ import annotations

from typing import Any

from app.services.script.beat_contract_auto_repair_common import (
    beat_screen_text,
    beat_text,
    compact,
    has_any,
    preferred_character,
    progression_action,
    progression_dialogue,
    progression_event,
    scene_screen_text,
    to_float,
    visible_len,
)

_VAGUE_VISUAL = ("气氛", "氛围", "紧张感", "压迫感")
_VAGUE = (
    "意识到",
    "明白",
    "内心",
    "崩溃",
    "发现关键线索",
    "关键线索",
    "出现转折",
    "发生反转",
    "制造冲突",
    "制造悬念",
    "留下悬念",
    "推动冲突",
    "升级冲突",
    "推进剧情",
)


def repair_beats(scene: dict[str, Any], beats: list[dict[str, Any]]) -> None:
    protagonist = preferred_character(beats) or "AP"
    for beat in beats:
        visible = str(beat.get("visible_event") or "")
        if has_any(visible, _VAGUE_VISUAL):
            beat["visible_event"] = f"{protagonist}停住脚步举起手机，云端日志时间戳映在屏幕上。"
        if (beat.get("beat_type") == "payoff" or beat.get("payoff_tag")) and has_any(
            visible, ("信任", "崩溃", "承认")
        ):
            beat["visible_event"] = "客户在会议纪要上签字确认继续项目，篡改者手机弹出解雇短信。"
            beat["payoff_tag"] = "客户签字继续项目"
        purpose = str(beat.get("dramatic_purpose") or "")
        if not purpose or has_any(purpose, _VAGUE):
            beat["dramatic_purpose"] = f"{beat['visible_event']}让证据链进入下一步。"
        for action in beat.get("action_lines") or []:
            if isinstance(action, dict) and has_any(
                str(action.get("content") or ""), _VAGUE_VISUAL
            ):
                action["content"] = "小陈横在门口按住平板，云端日志时间戳被蓝框锁定。"
    if protagonist.replace(" ", "") not in scene_screen_text(beats):
        beats[0].setdefault("action_lines", []).insert(
            0,
            {
                "content": f"{protagonist}把原始文件推到投影前，客户和团队同时看向屏幕。",
                "timing": "mid",
                "type": "action",
            },
        )
    if not any(beat.get("beat_type") == "payoff" or beat.get("payoff_tag") for beat in beats):
        target = beats[1 if len(beats) > 1 else 0]
        target["beat_type"] = "reveal"
        target["payoff_tag"] = "客户签字继续项目"
        target["visible_event"] = "客户在会议纪要上签字确认继续项目，AP把原始文件编号圈给镜头。"
    _ensure_recurring_dialogue(beats, protagonist)


def harden_opening_hook(beat: dict[str, Any] | None) -> None:
    if not isinstance(beat, dict):
        return
    beat["beat_type"] = "hook"
    if not has_any(beat_text(beat), ("异常", "倒计时", "删除", "危机", "证据", "反转", "改")):
        beat["visible_event"] = "客户拍桌质疑：投影数据被改了，原始文件证据与屏幕数字不符。"
        beat.setdefault("action_lines", []).insert(
            0,
            {
                "content": "投影数字变红，客户手指重重敲在错误数据上。",
                "timing": "0-2s",
                "type": "action",
            },
        )


def harden_final_cliffhanger(beat: dict[str, Any] | None) -> None:
    if not isinstance(beat, dict):
        return
    beat["beat_type"] = "cliffhanger"
    beat["visible_event"] = "AP手机弹出匿名短信：原始文件将在30秒后删除，下一个停职的是你。"
    beat["cliffhanger_tag"] = "匿名短信威胁删除原始文件"
    beat.setdefault("action_lines", []).append(
        {
            "content": "AP把手机举到镜头前，短信倒计时从30秒跳到29秒。",
            "timing": "outro",
            "type": "action",
        }
    )


def align_scene_durations(
    scene: dict[str, Any], beats: list[dict[str, Any]], opening: bool
) -> None:
    estimated = to_float(scene.get("estimated_duration_seconds")) or 0
    if estimated <= 0 or not beats:
        return
    first = min(3.0, max(1.0, estimated / len(beats))) if opening else 0.0
    if first:
        beats[0]["duration_seconds"] = round(first, 2)
    rest = beats[1:] if first else beats
    remaining = max(1.0, estimated - first)
    base = round(remaining / len(rest), 2)
    for index, beat in enumerate(rest):
        beat["duration_seconds"] = base if index < len(rest) - 1 else round(
            remaining - (base * index), 2
        )


def dedupe_progression(beats: list[dict[str, Any]]) -> None:
    seen_screen: set[str] = set()
    seen_lines: set[str] = set()
    protagonist = preferred_character(beats) or "AP"
    for beat in beats:
        state = compact(beat_screen_text(beat))
        if state in seen_screen:
            order = int(to_float(beat.get("order_index")) or len(seen_screen) + 1)
            beat["visible_event"] = progression_event(protagonist, order)
            beat["action_lines"] = [
                {
                    "content": progression_action(protagonist, order),
                    "timing": "mid",
                    "type": "action",
                }
            ]
            state = compact(beat_screen_text(beat))
        seen_screen.add(state)
        for line in beat.get("dialogue_lines") or []:
            if not isinstance(line, dict):
                continue
            text = compact(str(line.get("content") or ""))
            if text in seen_lines:
                line["content"] = progression_dialogue(
                    int(to_float(beat.get("order_index")) or 1)
                )
                text = compact(line["content"])
            seen_lines.add(text)


def shorten_dialogue_lines(beats: list[dict[str, Any]]) -> None:
    for beat in beats:
        for line in beat.get("dialogue_lines") or []:
            if isinstance(line, dict) and visible_len(str(line.get("content") or "")) > 15:
                line["content"] = _short_dialogue(str(line.get("content") or ""))


def _short_dialogue(text: str) -> str:
    replacements = (
        (("版本同步",), "可能是同步问题。"),
        (("会议纪要",), "纪要有你签字。"),
        (("刚才", "误会"), "刚才误会了。"),
        (("原始文件",), "原始文件在这。"),
        (("云端数据",), "云端875，投影920。"),
        (("左边", "右边"), "左云端，右投影。"),
        (("签过字",), "签字在这，怎么说？"),
    )
    for markers, replacement in replacements:
        if all(marker in text for marker in markers):
            return replacement
    for separator in ("。", "！", "？", "；", "，", ",", ":", "："):
        if separator in text:
            candidate = text.split(separator, 1)[0].strip(" ，,：:") + "。"
            if 4 <= visible_len(candidate) <= 15:
                return candidate
    return f"{compact(text)[:14]}。"


def _ensure_recurring_dialogue(
    beats: list[dict[str, Any]], protagonist: str
) -> None:
    covered = {
        beat.get("order_index")
        for beat in beats
        for line in beat.get("dialogue_lines", [])
        if isinstance(line, dict) and str(line.get("character") or "") == protagonist
    }
    for beat in beats:
        if len(covered) >= 2:
            break
        if beat.get("order_index") not in covered:
            beat.setdefault("dialogue_lines", []).append(
                {
                    "character": protagonist,
                    "content": progression_dialogue(int(beat["order_index"])),
                }
            )
            covered.add(beat.get("order_index"))
