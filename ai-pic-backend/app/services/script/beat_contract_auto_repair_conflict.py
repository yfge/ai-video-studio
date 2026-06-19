from __future__ import annotations

from typing import Any

from app.services.script.beat_contract_auto_repair_common import compact, has_any

_CONCRETE_OPPOSITION = (
    "系统",
    "客户",
    "日志",
    "倒计时",
    "锁",
    "删除",
    "篡改",
    "屏幕",
    "文件",
    "接口",
    "账单",
    "老板",
    "审片员",
    "内鬼",
)
_VAGUE = (
    "意识到",
    "明白",
    "内心",
    "崩溃",
    "发现关键线索",
    "关键线索",
    "冲突爆发",
    "数据不一致的发现",
    "出现转折",
    "发生反转",
    "信任崩溃",
    "紧张感",
    "潜在危机",
    "制造冲突",
    "制造悬念",
    "留下悬念",
    "推动冲突",
    "升级冲突",
    "推进剧情",
)
_ABSTRACT_OPPOSITION = ("幕后黑手", "神秘力量", "未知势力", "神秘人", "匿名威胁", "崩溃")
_THIN_OPPOSITION = {"篡改者", "内部篡改者", "内鬼", "同事", "团队成员"}


def repair_scene_conflict(scene: dict[str, Any]) -> None:
    conflict = scene.setdefault("conflict", {})
    if not isinstance(conflict, dict):
        conflict = {}
        scene["conflict"] = conflict
    conflict.setdefault("question", scene.get("summary") or "AP如何核实数据篡改？")
    stakes = str(conflict.get("stakes") or "")
    if has_any(stakes, _VAGUE) or not has_any(
        stakes, ("秒", "合同", "客户", "证据", "文件", "赔偿")
    ):
        conflict["stakes"] = "若不澄清，300万项目合同当场作废，客户终止签字验收。"
    opposition = str(conflict.get("opposition") or "")
    if (
        compact(opposition) in _THIN_OPPOSITION
        or has_any(opposition, _ABSTRACT_OPPOSITION)
        or not has_any(opposition, _CONCRETE_OPPOSITION)
    ):
        conflict["opposition"] = (
            "李明手机弹出解雇短信，AP手机显示30秒倒计时，原始文件删除威胁阻止核实。"
        )
    turn = str(conflict.get("turn") or "")
    if not turn or has_any(turn, _VAGUE):
        conflict["turn"] = "AP把投影数字、原始文件和团队反应对齐，锁定篡改来源。"
