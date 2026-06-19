from __future__ import annotations

from typing import Any

from app.services.script.beat_contract_auto_repair_common import (
    compact,
    has_any,
    preferred_character,
)


def needs_workplace_anchors(scenes: list[Any]) -> bool:
    text = compact(str(scenes))
    return has_any(
        text, ("合同", "客户", "并购", "尽调", "张总", "陈默", "小陈")
    ) and has_any(text, ("篡改", "时间戳", "日志", "原始文件", "投影"))


def apply_workplace_anchors(
    scene: dict[str, Any], beats: list[dict[str, Any]], index: int, count: int
) -> None:
    protagonist = preferred_character(beats) or "AP"
    if "AP" in protagonist or "回归" in protagonist:
        protagonist = "AP"
    if index == 0:
        data = [
            ("hook", "张总手机倒计时从60秒跳到59秒，投影并购数据被红框标出，与AP手里的原始文件差额300万。", ("张总", "60秒，合同作废！"), (protagonist, "数字不会撒谎。")),
            ("reveal", "AP把原始文件、云端日志时间戳并排投到屏幕，差额被红框圈出。", (protagonist, "看时间戳。"), ("小陈", "备份还在。")),
            ("conflict", "小陈锁定云端日志，陈默手指悬在删除确认键，张总倒计时跳到45秒。", ("小陈", "日志已锁。"), ("陈默", "先关投影！")),
        ]
    elif index == 1:
        data = [
            ("conflict", "陈默突然抢AP手机，通知栏露出改完给你20万，删除确认框停在红色按钮上。", ("陈默", "手机给我。"), (protagonist, "删除键别碰。")),
            ("reveal", "小陈把锁住的日志投屏，陈默昨晚23:41的账号记录被红框套住。", ("小陈", "账号是陈默。"), (protagonist, "录音也在。")),
            ("payoff", "陈默手机通知栏跳出“改完给你20万”，张总停止撤单电话。", ("张总", "15秒。"), ("陈默", "我被逼的。")),
        ]
    elif index == count - 1:
        data = [
            ("setup", "会议室刚安静，投影上的原始文件编号突然闪红。", (protagonist, "别关投影。"), ("小陈", "文件在变。")),
            ("conflict", "匿名账号开始远程删除原始文件，进度条从1%跳到7%。", ("小陈", "还有远程权限。"), (protagonist, "先保原件。")),
            ("cliffhanger", "AP手机弹出匿名短信：原始文件将在30秒后删除，下一个停职的是你。", (protagonist, "这只是第一层。"), (protagonist, "盯住倒计时。")),
        ]
    else:
        data = [
            ("reveal", "陈默手机弹出20万到账短信和女儿住院费威胁。", ("陈默", "他们逼我。"), (protagonist, "谁给的钱？")),
            ("conflict", "小陈把陈默账号、收款短信和删除时间排成三列。", ("小陈", "三列都对上。"), (protagonist, "时间线完整。")),
            ("reveal", "AP把录音波形暂停在陈默低声改数据的句子上。", (protagonist, "录音对上了。"), ("陈默", "我只是转发。")),
        ]
    for beat, item in zip(beats[:3], data):
        _set_beat(beat, *item, protagonist=protagonist)


def _set_beat(
    beat: dict[str, Any],
    beat_type: str,
    visible: str,
    first_line: tuple[str, str],
    second_line: tuple[str, str],
    *,
    protagonist: str,
) -> None:
    beat["beat_type"] = beat_type
    beat["visible_event"] = visible
    beat["dramatic_purpose"] = f"{visible}迫使客户和团队在屏幕前确认证据。"
    beat["action_lines"] = [
        {
            "content": f"{protagonist}把原始文件推到投影前，屏幕证据被镜头推近。",
            "timing": "mid",
            "type": "action",
        }
    ]
    beat["dialogue_lines"] = [
        {"character": first_line[0], "content": first_line[1]},
        {"character": second_line[0], "content": second_line[1]},
    ]
    if beat_type == "payoff":
        beat["payoff_tag"] = "客户签字继续项目"
    if beat_type == "cliffhanger":
        beat["cliffhanger_tag"] = "匿名短信威胁删除原始文件"
